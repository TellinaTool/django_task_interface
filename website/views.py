"""
This file defines functions to handle requests at URLs defined in urls.py.
"""

from django.http import HttpResponse, JsonResponse
from .models import *
from .filesystem import disk_2_dict

import time
import uuid
import datetime
import docker
import traceback
import time

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

def get_current_task_id(request):
    """
    Args:
        access_code

    Returns the task_id for the given user.
    """
    access_code = request.GET['access_code']
    task_manager = User.objects.get(access_code=access_code).task_manager
    return HttpResponse(str(task_manager.get_current_task_id()))

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
    access_code = request.GET['access_code']
    task_manager = User.objects.get(access_code=access_code).task_manager
    return JsonResponse(task_manager.get_filesystem())

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
    access_code = request.GET['access_code']
    task_manager = User.objects.get(access_code=access_code).task_manager
    task_manager.update_state()
    return HttpResponse('')

def fail():
    """
    Return a call to this function within a test request to send an HTML
    page with a traceback of where the failure occured.
    """
    msg = 'test failed: {}'.format(traceback.format_stack()[-2])
    return HttpResponse('<pre>{}</pre>'.format(msg))

def test(request):
    """
    Trigger this handler to run automated tests.

    This should be a proper unit test in website/tests.py, but the container
    cannot open a websocket to the test server started by the unit test
    framework, for some unknown reason.
    """

    cli = docker.Client(base_url='unix://var/run/docker.sock')

    # Test container creation
    filesystem_name = 'tellina_session_'+str(uuid.uuid4())
    filesystem = {'dir1': {'dir2': {'file2.txt': None}}, 'file1.txt': None}
    container = create_container(filesystem_name, filesystem)
    try:
        cli.inspect_container(container=container.container_id)
    except docker.errors.NotFound as e:
        return fail()

    # Check if filesystem was setup properly
    if disk_2_dict(pathlib.Path('/{}/home'.format(filesystem_name)))['home'] != filesystem:
        return fail()

    # Test container deletion
    container.destroy()
    is_container_destroyed = False
    try:
        cli.inspect_container(container=container.container_id)
    except docker.errors.NotFound as e:
        is_container_destroyed = True
    if not is_container_destroyed:
        return fail()

    # Create some tasks
    Task.objects.create(
        description='Print hello world.',
        type='stdout',
        initial_filesystem='{"dir1": {"dir2": {"file2.txt": null}}, "file1.txt": null}',
        answer='hello world',
        duration=datetime.timedelta(seconds=999999),
    )
    Task.objects.create(
        description='This should timeout almost immediately',
        type='stdout',
        initial_filesystem='{}',
        answer='hello world',
        duration=datetime.timedelta(milliseconds=1),
    )
    Task.objects.create(
        description='Remove the file foo.txt.',
        type='filesystem',
        initial_filesystem='{"foo.txt": null}',
        answer='{}',
        duration=datetime.timedelta(seconds=999999),
    )

    # Create a task manager
    task_manager = create_task_manager()

    # Check initial current task
    current_task_id = task_manager.get_current_task_id()
    if current_task_id != 1:
        return fail()

    # Check task result is in 'not_started'
    task_result = task_manager.get_current_task_result()
    if task_result.state != 'not_started':
        return fail()

    # Initialize to starting task
    session_id = task_manager.initialize_task(current_task_id)
    if session_id is None:
        return fail()

    # Check task result state == 'running'
    task_result = TaskResult.objects.filter(task_manager_id=task_manager.id).get(task_id=current_task_id)
    if task_result.state != 'running':
        return fail()

    # Wait a bit, then check if container's websocket connected to us
    time.sleep(0.5)
    task_manager.refresh_from_db()
    if task_manager.container_stdin_channel_name == '':
        return fail()

    # Write to container's STDIN
    task_manager.write_stdin(session_id, '''echo 'h'ello world\n''')

    # Wait a bit, then check container's STDOUT
    time.sleep(0.5)
    task_manager.refresh_from_db()
    if "echo 'h'ello world" not in task_manager.stdout:
        return fail()
    if "hello world" not in task_manager.stdout:
        return fail()

    # Update task manager state to trigger answer check
    task_manager.update_state()

    # The task should have passed
    if task_manager.check_task_state(1) != 'passed':
        return fail()

    # Check that we've moved onto the next task
    current_task_id = task_manager.get_current_task_id()
    if current_task_id != 2:
        return fail()
    if task_manager.check_task_state(2) != 'not_started':
        return fail()

    # Initialize next task
    session_id = task_manager.initialize_task(2)
    if task_manager.check_task_state(2) != 'running':
        return fail()

    # Wait a bit, and update task manager state to trigger timeout check
    time.sleep(0.5)
    task_manager.update_state()

    # The task should have timed out
    if task_manager.check_task_state(2) != 'timed_out':
        return fail()

    # Check that we've moved onto next task
    if task_manager.get_current_task_id() != 3:
        return fail()
    if task_manager.check_task_state(3) != 'not_started':
        return fail()

    # Initialize task
    session_id = task_manager.initialize_task(3)
    if task_manager.check_task_state(3) != 'running':
        return fail()

    # Wait a bit, write to container's STDIN
    time.sleep(0.5)
    if not task_manager.write_stdin(session_id, 'rm foo.txt\n'):
        return fail()

    # Check that task passed
    time.sleep(0.5)
    if task_manager.get_filesystem() != {}:
        return fail()
    task_manager.update_state()
    if task_manager.check_task_state(3) != 'passed':
        return fail()

    return HttpResponse('Tests passed')
