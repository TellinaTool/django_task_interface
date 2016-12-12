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

def fail():
    msg = 'test failed: {}'.format(traceback.format_stack()[-2])
    return HttpResponse('<pre>{}</pre>'.format(msg))

def test_task_manager(request):
    cli = docker.Client(base_url='unix://var/run/docker.sock')

    # Test container creation
    filesystem_name = 'tellina_session_'+str(uuid.uuid4())
    container = create_container(filesystem_name)
    try:
        cli.inspect_container(container=container.container_id)
    except docker.errors.NotFound as e:
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
        initial_filesystem='{}',
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
        duration=datetime.timedelta(seconds=1),
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

    # Wait a bit, and update task manager state to trigger timeout check
    time.sleep(0.5)
    task_manager.update_state()

    # The task should have timed out
    if task_manager.check_task_state(2) != 'timed_out':
        return fail()

    return HttpResponse('Tests passed')
