"""
This file defines functions to handle requests at URLs defined in urls.py.
"""

from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .filesystem import disk_2_dict

from . import functions
import http.cookies
import uuid
import datetime
import docker
import traceback
import time

def session_id_required(f):
    @functions.wraps(f)
    def g(request, *args, **kwargs):
        session_id = request.COOKIES['session_id']
        return f(request, *args, session_id=session_id, **kwargs)
    return g

def task_session_id_required(f):
    @functions.wraps(f)
    def g(request, *args, **kwargs):
        session_id = request.COOKIES['session_id']
        task_session_id = request.COOKIES['task_session_id']
        # ensure that the task session id matches with the study session id
        assert(task_session_id.startswith(session_id))
        return f(request, *args, task_session_id=task_session_id, **kwargs)
    return g

def get_task_session_id(study_session_id, num_tasks_completed):
    return study_session_id + '/task-{}'.format(num_tasks_completed + 1)

# --- Task Management --- #

@session_id_required
def get_container_port(request, session_id):
    """

    Args:
        session_id

    Returns the session_id and container_port for the given user.

    """
    container_port = StudySession.objects.get(session_id=session_id).container.port
    return JsonResponse({
        "container_port": container_port
    })

@task_session_id_required
def get_task_duration(request, task_session_id):
    """

    Args:
        task_session_id:

    Returns the maximum time length the user is allowed to spend on the task.

    """
    task_session = TaskSession.objects.get(session_id=task_session_id)
    return JsonResponse({
        "duration": task_session.task.duration.seconds
    })

@task_session_id_required
def go_to_next_task(request, task_session_id):
    """
    Args:

        task_session_id:

    Create a new task session.
    """

    # close current_task_session
    current_task_session = TaskSession.objects.get(session_id=task_session_id)
    current_task_session.end_time = timezone.now()
    current_task_session.status = request.GET['reason_for_close']
    current_task_session.save()

    study_session = current_task_session.study_session
    study_session.num_tasks_completed += 1

    # check for user study completion
    num_tasks_completed = study_session.num_tasks_completed
    if num_tasks_completed == study_session.total_num_tasks:
        close_study_session(study_session, 'finished')
        return JsonResponse({
            "status": 'STUDY_SESSION_COMPLETE'
        })

    # wipe out everything in the user's home directory
    user_name = "myuser"
    container = study_session.container
    subprocess.run(['docker', 'exec', '-u', 'root', container.container_id,
        'rm', '-r', '/home/{}'.format(user_name)])

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

    resp = JsonResponse({
        'status': 'RUNNING',
        "task_session_id": next_task_session_id
    })
    resp.set_cookie('task_session_id', next_task_session_id)
    return resp

@task_session_id_required
def get_current_task(request, task_session_id):
    """
    Args:
        task_session_id

    Returns the
        - description
        - goal directory
        - order number in the study session
    of the currently served task in the user's study session.
    """
    task_session = TaskSession.objects.get(session_id=task_session_id)
    task = task_session.task

    study_session = task_session.study_session
    order_number = study_session.num_tasks_completed + 1

    # Initialize filesystem
    container = study_session.container
    dict_2_disk(json.loads(task.initial_filesystem),
                pathlib.Path('/{}/home'.format(container.filesystem_name)))

    context = {
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

# --- File System Management --- #

@task_session_id_required
def reset_file_system(request, task_session_id):
    """
    Args:
        task_session_id:

    Reset the file system of the current task session.
    """
    task_session = TaskSession.objects.get(session_id=task_session_id)
    study_session = task_session.study_session
    container = study_session.container
    container_id = container.container_id

    # wipe out everything in the user's home directory and reinitialize
    user_name = "myuser"
    subprocess.run(['docker', 'exec', '-u', 'root', container_id,
        'rm', '-r', '/home/{}'.format(user_name)])

    # re-initialize file system
    task = task_session.task
    dict_2_disk(json.loads(task.initial_filesystem),
                pathlib.Path('/{}/home'.format(container.filesystem_name)))

    return JsonResponse({
        'container_id': container_id
    })

# --- Study Session Management --- #
def close_study_session(session, reason_for_close):
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
        return JsonResponse({
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
        return JsonResponse({
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
        else:
            # close previous running sessions if not properly closed
            pass

        if check_existing_session == "false" or no_existing_session:
            # register a new study session for the user
            session_id = '-'.join([access_code, "study_session",
                str(StudySession.objects.filter(user=user).count() + 1)])
            init_task_session_id = get_task_session_id(session_id, 0)

            # create the container of the study session
            user_name = "myuser"
            container = create_container(session_id, user_name)

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

            resp = JsonResponse({
                "status": "SESSION_CREATED",
                "task_session_id": init_task_session_id,
            })

            # remember the study session id and the task session id with cookies
            resp.set_cookie('session_id', session_id)
            resp.set_cookie('task_session_id', init_task_session_id)

    except ObjectDoesNotExist:
        resp = JsonResponse({
            'status': 'USER_DOES_NOT_EXIST'
        })

    return resp

def retrieve_access_code(request):
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']
    try:
        access_code = User.objects.get(first_name=first_name,
                                       last_name=last_name)
        return JsonResponse({
            "access_code": access_code
        })
    except ObjectDoesNotExist:
        return JsonResponse({
            "access_code": 'USER_DOES_NOT_EXIST'
        })

