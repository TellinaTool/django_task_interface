"""
This file defines functions to handle requests at URLs defined in urls.py.
"""

from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .filesystem import dict_2_disk, disk_2_dict
from .constants import *

from . import functions
import http.cookies
import uuid
import datetime
import docker
import traceback
import time
import subprocess

def get_task_session_id(study_session_id, num_tasks_completed):
    return study_session_id + '/task-{}'.format(num_tasks_completed + 1)

def json_response(d={}, status='SUCCESS'):
    d.update({'status': status})
    resp = JsonResponse(d)
    return resp

def session_id_required(f):
    @functions.wraps(f)
    def g(request, *args, **kwargs):
        session_id = request.COOKIES['session_id']
        try:
            study_session = StudySession.objects.get(session_id=session_id)
            return f(request, *args, study_session=study_session, **kwargs)
        except ObjectDoesNotExist:
            return json_response(status='STUDY_SESSION_DOES_NOT_EXIST')
    return g

def task_session_id_required(f):
    @functions.wraps(f)
    def g(request, *args, **kwargs):
        session_id = request.COOKIES['session_id']
        task_session_id = request.COOKIES['task_session_id']
        # ensure that the task session id matches with the study session id
        if not task_session_id.startswith(session_id):
            return json_response(
                status='STUDY_SESSION_AND_TASK_SESSION_MISMATCH')
        try:
            task_session = TaskSession.objects.get(session_id=task_session_id)
            return f(request, *args, task_session=task_session, **kwargs)
        except ObjectDoesNotExist:
            return json_response(status='TASK_SESSION_DOES_NOT_EXIST')
    return g

# --- Task Management --- #

@session_id_required
def get_container_port(request, study_session):
    """

    Args:
        study_session

    Returns the session_id and container_port for the given user.

    """
    container_port = study_session.container.port
    return json_response({
        "container_port": container_port
    })

@task_session_id_required
def get_task_duration(request, task_session):
    """

    Args:
        task_session:

    Returns the maximum time length the user is allowed to spend on the task.

    """
    return json_response({
        "duration": task_session.task.duration.seconds
    })

@task_session_id_required
def go_to_next_task(request, task_session):
    """
    Args:

        task_session:

    Create a new task session.
    """

    current_task_session = task_session
    study_session = current_task_session.study_session

    # if a task session has ended, ignore requests for updating task attributes
    if current_task_session.status == 'running':
        # close current_task_session
        current_task_session.end_time = timezone.now()
        current_task_session.status = request.GET['reason_for_close']
        current_task_session.save()
        study_session.num_tasks_completed += 1

    # check for user study completion
    num_tasks_completed = study_session.num_tasks_completed
    assert(num_tasks_completed <= study_session.total_num_tasks)
    if num_tasks_completed == study_session.total_num_tasks:
        close_study_session(study_session, 'finished')
        resp = json_response(status='STUDY_SESSION_COMPLETE')
        resp.set_cookie('session_id', '')
        resp.set_cookie('task_session_id', '')
    else:
        # wipe out everything in the user's home directory
        container = study_session.container
        subprocess.run(['docker', 'exec', '-u', 'root', container.container_id,
            'rm', '-r', '/home/{}'.format(USER_NAME)])

        next_task_session_id = get_task_session_id(study_session.session_id,
                                                   num_tasks_completed)
        study_session.current_task_session_id = next_task_session_id
        study_session.save()

        TaskSession.objects.create(
            study_session = study_session,
            session_id = next_task_session_id,
            task = pick_task(num_tasks_completed=num_tasks_completed),
            start_time = timezone.now(),
            status = 'running'
        )

        resp = json_response({"task_session_id": next_task_session_id},
                             status='RUNNING')
        resp.set_cookie('task_session_id', next_task_session_id)

    return resp

@task_session_id_required
def get_current_task(request, task_session):
    """
    Args:
        task_session

    Returns the
        - description
        - goal directory
        - order number in the study session
    of the currently served task in the user's study session.
    """
    task = task_session.task

    study_session = task_session.study_session
    order_number = study_session.num_tasks_completed + 1

    # Initialize filesystem
    container = study_session.container
    container_id = container.container_id
    filesystem_status = dict_2_disk(json.loads(task.initial_filesystem),
                pathlib.Path('/{}/home'.format(container.filesystem_name)))
    subprocess.call(['docker', 'exec', '-u', 'root', container_id,
        'chown', '-R', '{}:{}'.format(USER_NAME, USER_NAME),
        '/home/{}'.format(USER_NAME)])

    context = {
        "status": filesystem_status,
        "task_description": task.description,
        "task_goal": task.goal,
        "task_order_number": order_number,
        "total_num_tasks": study_session.total_num_tasks,
        "first_name": study_session.user.first_name,
        "last_name": study_session.user.last_name
    }

    template = loader.get_template('task.html')
    return HttpResponse(template.render(context, request))


def pick_task(num_tasks_completed):
    """
    Pick a task from the database for the user to work on next.
    """
    if PART_I_TASKS is not None:
        if num_tasks_completed < len(PART_I_TASKS):
            # user is in the first part of the study
            task_id = PART_I_TASKS[num_tasks_completed]
        else:
            # user is in the second part of the study
            task_id = PART_II_TASKS[num_tasks_completed - len(PART_I_TASKS)]
    else:
        # randomly select an unseen task from the database
        raise NotImplementedError

    task = Task.objects.get(task_id=task_id)
    return task

# --- Terminal I/O Management --- #
@task_session_id_required
@csrf_exempt
def on_command_execution(request, task_session):
    """
    Args:
        task_session:

    Record user's terminal standard output upon command execution. Check for
    task completion.
    """
    task = task_session.task
    stdout = request.POST['stdout']

    ActionHistory.objects.create(
        task_session=task_session,
        action = stdout,
        action_time = timezone.now()
    )

    if task.type == 'stdout':
        # check if stdout signals task completion
        if task.goal in stdout:
            return json_response(status='TASK_COMPLETED')
    elif task.type == 'filesystem':
        # check if the current file system is the same as the goal file system
        study_session = task_session.study_session
        container = study_session.container
        current_file_system = disk_2_dict(
            pathlib.Path('/{}/home'.format(container.filesystem_name)))['home']
    else:
        raise AttributeError('Unrecognized task type "{}": must be "stdout" or'
                             '"filesystem"'.format(task.type))

    return json_response()

# --- File System Management --- #

@task_session_id_required
def reset_file_system(request, task_session):
    """
    Args:
        task_session:

    Reset the file system of the current task session.
    """
    study_session = task_session.study_session
    container = study_session.container
    container_id = container.container_id

    # wipe out everything in the user's home directory and reinitialize
    subprocess.call(['docker', 'exec', '-u', 'root', container_id,
        'rm', '-r', '/home/{}'.format(USER_NAME)])

    # re-initialize file system
    task = task_session.task
    filesystem_status = dict_2_disk(json.loads(task.initial_filesystem),
                pathlib.Path('/{}/home'.format(container.filesystem_name)))
    subprocess.call(['docker', 'exec', '-u', 'root', container_id,
        'chown', '-R', '{}:{}'.format(USER_NAME, USER_NAME),
        '/home/{}'.format(USER_NAME)])

    return json_response({'container_id': container_id},
                         status=filesystem_status)

# --- Study Session Management --- #
def close_study_session(session, reason_for_close):
    # ignore already closed study sessions
    if session.status == 'running' or session.status == 'paused':
        session.current_task_session_id = ''
        session.status = reason_for_close
        session.save()

        # destroy the container associated with the study session
        session.container.destroy()

# --- User Login --- #

def register_user(request):
    """
    Args:
        first_name
        last_name

    Returns "USER_EXISTS" message if the user is already registered in the
    database, otherwise, returns the system-wise unique access code for the
    user.
    """
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']

    if User.objects.filter(first_name=first_name, last_name=last_name).exists():
        return json_response({
            'access_code': 'USER_EXISTS'
        })
    else:
        # make access code for user
        access_code = first_name.lower() + '-' + last_name.lower()
        user = User.objects.create(
            first_name = first_name,
            last_name = last_name,
            access_code = access_code
        )
        return json_response({
            'access_code': access_code
        })

def user_login(request):
    """

    Args:
        access_code
        check_existing_session

    Create a container for the new study session.

    """
    access_code = request.GET['access_code']
    check_existing_session = request.GET['check_existing_session']
    try:
        user = User.objects.get(access_code=access_code)

        # check if an incomplete study session for the user exists
        if check_existing_session == "true":
            no_existing_session = False
            sessions = StudySession.objects.filter(user=user, status='running')
            if sessions.exists():
                # close previous running sessions if not properly closed
                existing_sessions = list(sessions.order_by('creation_time'))
                for session in existing_sessions[:-1]:
                    close_study_session(session, 'closed_with_error')
                session = existing_sessions[-1]
                # remember the study session id and the task session id with cookies
                resp = JsonResponse({
                    "status": "RUNNING_STUDY_SESSION_FOUND",
                    "task_session_id": session.current_task_session_id,
                })
                resp.set_cookie('session_id', session.session_id)
                resp.set_cookie('task_session_id', session.current_task_session_id)
            else:
                no_existing_session = True

        if check_existing_session == "false" or no_existing_session:
            # register a new study session for the user
            session_id = '-'.join([access_code, "study_session",
                str(StudySession.objects.filter(user=user).count() + 1)])
            init_task_session_id = get_task_session_id(session_id, 0)

            # create the container of the study session
            container = create_container(session_id)

            session = StudySession.objects.create(
                user = user,
                session_id = session_id,
                container = container,
                creation_time = timezone.now(),

                current_task_session_id = init_task_session_id,
                status = 'running'
            )

            # initialize the first task session
            TaskSession.objects.create(
                study_session = session,
                session_id = init_task_session_id,
                task = pick_task(num_tasks_completed = 0),
                start_time = timezone.now(),
                status = 'running'
            )

            resp = json_response({"task_session_id": init_task_session_id},
                                 status="SESSION_CREATED")

            # remember the study session id and the task session id with cookies
            resp.set_cookie('session_id', session_id)
            resp.set_cookie('task_session_id', init_task_session_id)

    except ObjectDoesNotExist:
        resp = json_response(status='USER_DOES_NOT_EXIST')

    return resp

def retrieve_access_code(request):
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']
    try:
        access_code = User.objects.get(first_name=first_name,
                                       last_name=last_name).access_code
        return JsonResponse({
            "access_code": access_code
        })
    except ObjectDoesNotExist:
        return JsonResponse({
            "access_code": 'USER_DOES_NOT_EXIST'
        })

