"""
This file defines functions to handle requests at URLs defined in urls.py.
"""

from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from .models import *
from .filesystem import disk_2_dict

import http.cookies
import uuid
import datetime
import docker
import traceback
import time
import werkzeug


# --- Task Management --- #

def start_task(request):
    """Start a new task session."""
    template = loader.get_template('task.html')
    context = {}
    return HttpResponse(template.render(context, request))


def get_task(request):
    """
    Args:
        task_id

    Returns a JSON object of the task
    """
    # NOTE: This exposes the full task object, including the answer field.
    # You'll probably want to change this to only expose the task description.
    task_id = int(request.GET['task_id'])
    task = Task.objects.get(id=task_id)
    return JsonResponse(task.to_dict())

def get_container_port(request):
    """
    Args:
        access_code

    Returns the task_id for the given user.
    """
    session_id = request.COOKIES['session_id']
    container_port = StudySession.objects.get(session_id=session_id).container.port
    return JsonResponse({
        "container_port": container_port
    })

def initialize_task(request):
    """
    Args:
        access_code
        task_id

    Clears any existing session and initializes a new session for the given task_id.
    """
    access_code = request.GET['access_code']
    task_id =  int(request.GET['task_id'])
    task_manager = User.objects.get(access_code=access_code).task_manager
    session_id = task_manager.initialize_task(task_id)
    if session_id is None:
        return HttpResponse('wrong_task')
    else:
        return HttpResponse(session_id)

def get_filesystem(request):
    """
    Args:
        access_code

    Returns JSON representation of the user's current home directory.
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

# --- User Login --- #

def register_user(request):
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
    access_code = request.GET['access_code']
    try:
        user = User.objects.get(access_code=access_code)

        # register a new study session for the user
        session_id = '-'.join([access_code, "study_session",
            str(StudySession.objects.filter(user=user).count() + 1)])

        container = create_container(session_id)

        session = StudySession.objects.create(
            user = user,
            session_id = session_id,
            status = 'running',
            container = container
        )

        """
        A study session handles logic related to starting, stopping, and
        resetting tasks.

        Each method of StudySession acquires/releases a file lock so that
        concurrent method calls are serialized.
        """

        resp = JsonResponse({
            "status": "SESSION_CREATED",
            "session_id": session_id
        })
        # remember session id with cookie
        resp.set_cookie('session_id', session_id)
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

