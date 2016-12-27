"""
This file defines functions to handle requests at URLs defined in urls.py.
"""

from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .filesystem import disk_2_dict

import http.cookies
import uuid
import datetime
import docker
import traceback
import time


# --- Task Management --- #

def task(request):
    """
    Start a new task session.
    """
    template = loader.get_template('task.html')
    context = {}
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

def initialize_task(request):
    """
    Args:
        access_code
        task_id

    Clears any existing session and initializes a new session for the given
    task_id.
    """
    access_code = request.GET['access_code']
    task_id =  int(request.GET['task_id'])
    task_manager = User.objects.get(access_code=access_code).task_manager
    session_id, port = task_manager.initialize_task(task_id)
    if session_id is None:
        return HttpResponse(status=400)
    else:
        return JsonResponse({'session_id': session_id, 'port': port})

def get_filesystem(request):
    """
    Args:
        access_code

    Returns the JSON representation of the user's current home directory.
    """
    session_id = request.COOKIES['session_id']
    # task_manager = User.objects.get(access_code=access_code).task_manager
    # filesystem = task_manager.get_filesystem()
    # if filesystem is None:
    #     return HttpResponse('no_filesystem_available')
    # else:
    #     return JsonResponse(filesystem)
    return HttpResponse('')

def check_task_state(request):
    """
    Args:
        access_code
        task_id

    Returns the state of the TaskResult for the given user and task_id.
    """
    access_code = request.GET['access_code']
    task_id =  int(request.GET['task_id'])
    task_manager = User.objects.get(access_code=access_code).task_manager
    return HttpResponse(task_manager.check_task_state(task_id))

def update_state(request):
    """
    Args:
        access_code

    Triggers an update of TaskManager's state.
    """
    if 'session_id' in request.COOKIES:
        session_id = request.COOKIES['session_id']
    # task_manager = User.objects.get(access_code=access_code).task_manager
    # task_manager.update_state()
    return HttpResponse('')


@csrf_exempt
def append_stdin(request):
    """
    POST

    Query parameters:
        access_code
        session_id

    Request body: data to add to stdin

    Appends request body to session's standard input.
    """
    access_code = request.GET['access_code']
    session_id = request.GET['session_id']

    task_manager = User.objects.get(access_code=access_code).task_manager
    if task_manager.append_stdin(session_id, str(request.body)):
        return HttpResponse()
    else:
        return HttpResponse(status=400)

@csrf_exempt
def append_stdout(request):
    access_code = request.GET['access_code']
    session_id = request.GET['session_id']

    task_manager = User.objects.get(access_code=access_code).task_manager
    if task_manager.append_stdout(session_id, str(request.body)):
        return HttpResponse()
    else:
        return HttpResponse(status=400)

def fail():
    """
    Return a call to this function within a test request to send an HTML
    page with a traceback of where the failure occured.
    """
    msg = 'test failed: {}'.format(traceback.format_stack()[-2])
    return HttpResponse('<pre>{}</pre>'.format(msg))


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

    try:
        user = User.objects.get(first_name=first_name, last_name=last_name)
        return JsonResponse({
            'access_code': 'USER_EXISTS'
        })
    except ObjectDoesNotExist:
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

    Create a container for the new study session.

    """
    access_code = request.GET['access_code']
    try:
        user = User.objects.get(access_code=access_code)

        # register a new study session for the user
        session_id = '-'.join([access_code, "study_session",
            str(StudySession.objects.filter(user=user).count() + 1)])
        init_task_session_id = session_id + '/task-1'

        # create the container of the study session
        container = create_container(session_id)

        session = StudySession.objects.create(
            user = user,
            session_id = session_id,
            container = container,

            current_task_session = init_task_session_id,
            status = 'running'
        )

        # initialize the first task session
        TaskSession.objects.create(
            study_session = session,
            session_id = init_task_session_id,
            task = pick_task(num_tasks_completed = 0),
            start_time = datetime.datetime.now(),
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

def get_container_port(request):
    """

    Args:
        session_id

    Returns the session_id and container_port for the given user.

    """
    session_id = request.COOKIES['session_id']
    container_port = StudySession.objects.get(session_id=session_id).container.port
    return JsonResponse({
        "container_port": container_port
    })


def get_task(request):
    """
    Args:
        session_id

    Returns the
        - description
        - goal directory
        - number in the study session
    of the currently served task in the user's study session.
    """
    session_id = request.COOKIES['session_id']
    study_session = StudySession.objects.get(session_id=session_id)
    user = study_session.user

    # decide which task to return
    num_tasks_completed = study_session.num_tasks_completed
    treatment_order = user.treatment_order




    task_id = int(request.GET['task_id'])
    task = Task.objects.get(id=task_id)
    return JsonResponse(task.to_dict())
