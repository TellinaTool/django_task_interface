from django.http import HttpResponse
from .models import *

import time
import uuid
import datetime
import docker
import traceback
import time

def test(request):
    # This should be a proper unit test in website/tests.py, but the container
    # cannot open a websocket to the test server started by the unit test, for
    # some unknown reason.
    container = create_container(str(uuid.uuid4()))
    time.sleep(2) # wait for container's websocket to connect to us
    container.refresh_from_db() # reload object from database
    print(container.stdout) # expect: this should print the initial terminal prompt
    container.write_stdin('ls\n') # send 'ls' command
    time.sleep(2) # wait for container to send STDOUT
    container.refresh_from_db()
    print(container.stdout) # expect: this should print the result of 'ls'
    container.destroy()

    return HttpResponse("Test done. Received following STDOUT: {}".format(container.stdout))

def test_task_manager(request):
    cli = docker.Client(base_url='unix://var/run/docker.sock')

    # Test container creation
    filesystem_name = 'tellina_session_'+str(uuid.uuid4())
    container = create_container(filesystem_name)
    try:
        cli.inspect_container(container=container.container_id)
    except docker.errors.NotFound as e:
        return HttpResponse('test fail: {}'.format(traceback.format_stack()))

    # Test container deletion
    container.destroy()
    is_container_destroyed = False
    try:
        cli.inspect_container(container=container.container_id)
    except docker.errors.NotFound as e:
        is_container_destroyed = True
    if not is_container_destroyed:
        return HttpResponse('test fail: {}'.format(traceback.format_stack()))

    # Create some tasks
    Task.objects.create(
        description='Print hello world.',
        type='stdout',
        initial_filesystem='{}',
        answer='hello world',
        duration=datetime.timedelta(seconds=1),
    )
    Task.objects.create(
        description='Remove the file foo.txt.',
        type='filesystem',
        initial_filesystem='{"foo.txt": null}',
        answer='{}',
        duration=datetime.timedelta(seconds=1),
    )

    # Create a task manager
    task_manager = create_task_manager(Task.objects.all())

    # Check initial current task
    current_task_id = task_manager.get_current_task_id()
    if current_task_id != 1:
        return HttpResponse('test fail: {}'.format(traceback.format_stack()))


    # Check task result is in 'not_started'
    task_result = TaskResult.objects.filter(task_manager_id=task_manager.id).get(task_id=current_task_id)
    if task_result.state != 'not_started':
        return HttpResponse('test fail: {}'.format(traceback.format_stack()))

    # Initialize to starting task
    session_id = task_manager.initialize_task(current_task_id)
    if session_id is None:
        return HttpResponse('test fail: {}'.format(traceback.format_stack()))

    # Check task result state == 'running'
    task_result = TaskResult.objects.filter(task_manager_id=task_manager.id).get(task_id=current_task_id)
    if task_result.state != 'running':
        return HttpResponse('test fail: {}'.format(traceback.format_stack()))

    # Wait a bit for container's websocket to connect to us
    time.sleep(1)
    task_manager.refresh_from_db()
    if task_manager.container_stdin_channel_name == '':
        return HttpResponse('test fail: {}'.format(traceback.format_stack()))

    return HttpResponse('tests passed')
