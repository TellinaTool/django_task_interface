from django.db import models
from django.utils import timezone
from channels import Channel
from .filesystem import dict_2_disk, disk_2_dict

import docker
import requests
import os
import time
import subprocess
import uuid
import fcntl
import datetime
import pathlib
import json
from typing import Optional

class Container(models.Model):
    """Describes information about a running Docker container."""

    """The name of the virtual filesystem.

    The virtual filesystem that backs this container's home directory is
    located at /{filesystem_name}/home.
    """
    filesystem_name = models.TextField()

    """The ID of the container assigned by Docker."""
    container_id = models.TextField()

    """The host port through which the server in the container can be accessed."""
    port = models.IntegerField()

    def destroy(self):
        """Destroys container, filesystem, and database entry."""

        # Destroy Docker container
        subprocess.run(['docker', 'rm', '-f', self.container_id])
        # Destroy filesystem
        subprocess.run(['/bin/bash', 'delete_filesystem.bash', self.filesystem_name])
        # Delete table entry
        self.delete()

def create_container(filesystem_name: str, filesystem: dict) -> Container:
    """
    Creates a container whose filesystem is located at /{filesystem_name}/home
    on the host. The contents of filesystem are written to
    /{filesystem_name}/home.

    filesystem is a JSON representation of a filesystem.
    """

    # Make virtual filesystem
    subprocess.run(['/bin/bash', 'make_filesystem.bash', filesystem_name])

    # Initialize filesystem
    dict_2_disk(filesystem, pathlib.Path('/{}/home'.format(filesystem_name)))

    # Create Docker container
    # NOTE: the created container does not run yet
    cli = docker.Client(base_url='unix://var/run/docker.sock')
    docker_container = cli.create_container(
        image='tellina',
        ports=[10411],
        volumes=['/home/myuser'],
        host_config=cli.create_host_config(
            binds={
                '/{}/home'.format(filesystem_name): {
                    'bind': '/home/myuser',
                    'mode': 'rw',
                },
            },
            port_bindings={10411: ('127.0.0.1',)},
        ),
    )

    # Get ID of created container
    container_id = docker_container['Id']

    # Start container
    cli.start(container=container_id)

    # Find what port the container was mapped to
    info = cli.inspect_container(container_id)
    port = info['NetworkSettings']['Ports']['10411/tcp'][0]['HostPort']

    # Wait a bit for container's server to start
    time.sleep(1)

    # Create container model object
    container = Container.objects.create(
        filesystem_name=filesystem_name,
        container_id=container_id,
        port=port,
    )

    return container

class Task(models.Model):
    """Describes a task that a study participant must complete."""

    """The type of task. Can be 'stdout' or 'filesystem'."""
    type = models.TextField()

    """A human-readable description of the task."""
    description = models.TextField()

    """JSON representation of the user's starting home directory structure."""
    initial_filesystem = models.TextField()

    """
    The answer to the task.
    If type == 'stdout': expected string to be found in STDOUT
    If type == 'filesystem': JSON representation of what the user's home
    directory should look like.
    """
    answer = models.TextField()

    """How much time is alotted for the task."""
    duration = models.DurationField()

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the task."""
        answer = None
        if self.type == 'filesystem':
            answer = json.loads(self.answer)
        elif self.type == 'stdout':
            answer = self.answer
        else:
            raise Exception('unrecognized task type')
        return {
            'type': self.type,
            'description': self.description,
            'initial_filesystem': json.loads(self.initial_filesystem),
            'answer': answer,
            'duration': self.duration.seconds,
        }

class TaskResult(models.Model):
    """Describes the current state and completion results of a task.

    Each TaskResult is associated with 1 User, since a User has-one
    TaskManager and a TaskManager has-many TaskResult's.

    For example, if there are 2 tasks and 3 users, there are a total of 6
    task results - 2 for each user.
    """

    """The task that this TaskResult is associated with"""
    task = models.ForeignKey('Task', on_delete=models.CASCADE)

    """Each TaskResult belongs to a TaskManager"""
    task_manager = models.ForeignKey('TaskManager', on_delete=models.CASCADE)

    """A transcript of all STDIN for this task."""
    stdin = models.TextField()

    """A transcript of all STDOUT for this task."""
    stdout = models.TextField()

    """The time at which this task was started."""
    start_time = models.DateTimeField()

    """
    The state of the task result.

    Values:
        - 'not_started': The user has not started the task yet
        - 'running':     The user has started the task, but the task has not
                         passed nor timed out yet
        - 'timed_out':   The user started the task and did not pass it before
                         running out of time
        - 'passed':      The user started the task and passed it
    """
    state = models.TextField()

    """How long a user spent doing the task"""
    time_spent = models.DurationField()

    def end_time(self) -> datetime.datetime:
        """The time at which this task times out."""
        return self.start_time + self.task.duration

class SessionID(models.Model):
    """Used by TaskManager to create application-wide unique session IDs."""
    pass

def generate_session_id() -> str:
    """Generates a database-wide unique ID."""
    session_id = SessionID.objects.create()
    return str(session_id.id)

class TaskManager(models.Model):
    """Handles logic related to starting, stopping, and resetting tasks.

    Each User has-one TaskManager.

    Each method of TaskManager acquires/releases a file lock so that concurrent
    method calls are serialized.
    """

    """
    Prefix to be used in naming lock files.
    """
    LOCK_FILE_PREFIX = 'task_manager_lock_'

    """
    Either the current task running, or the next unstarted task to be run.
    -1 means that all tasks are done.
    """
    task_id = models.IntegerField()

    """
    A session is
        - an instance of a Docker container
        - the WebSocket from the container to this server
        - the WebSocket from the user to this server
        - a transcript of the STDIN sent from the user to the container
        - a transcript of the STDOUT sent from the container to the user

    A session is associated with 1 TaskResult.
    Each TaskManager can have 0 or 1 sessions at a time.
    1 or more sessions may be used while running a task.

    The following fields are associated with a session:
    """

    """
    Unique identifier for this session.
    '' means there is no current active session.
    """
    session_id = models.TextField()

    """The STDIN transcript for the current session."""
    stdin = models.TextField()

    """The STDOUT transcript for the current session."""
    stdout = models.TextField()

    """The ID of the Container model associated with this session."""
    container_id = models.IntegerField()              # -1 means no container

    """
    The name of the Channel connected to the container's STDIN.
    See consumers.py for how this Channel is registered with TaskManager.
    '' means this channel has not been registered.
    """
    container_stdin_channel_name = models.TextField() # '' means websocket not connected yet

    """
    The name of the Channel connected to xterm's STDOUT.
    See consumers.py for how this Channel is registered with TaskManager.
    '' means this channel has not been registered.
    """
    xterm_stdout_channel_name = models.TextField()    # '' means websocket not connected yet

    def lock(self):
        """
        Acquire file lock and refresh the model from the database.
        Does nothing if lock is already acquired.
        """
        with open('{}{}'.format(self.LOCK_FILE_PREFIX, self.id), 'w+') as file:
            fcntl.flock(file, fcntl.LOCK_EX)
        self.refresh_from_db()

    def unlock(self):
        """
        Release the file lock.
        Does nothing if lock is not held.
        """
        with open('{}{}'.format(self.LOCK_FILE_PREFIX, self.id), 'w+') as file:
            fcntl.flock(file, fcntl.LOCK_UN)

    def get_current_task_id(self) -> int:
        """
        Retrieves the current task's ID.
        """
        self.lock()
        task_id = self.task_id
        self.unlock()
        return task_id

    def initialize_task(self, task_id: int) -> Optional[str]:
        """
        Destroys current session and starts a new session for the specified task.

        Returns:
            ID of newly created session
            or None if task_id does not match self.task_id.
        """

        self.lock()
        if task_id == self.task_id: # Reset or start the current task
            # Destroy container, if any
            if self.container_id != -1:
                Container.objects.get(id=self.container_id).destroy()

            # Create a new session ID
            self.session_id = 'tellina_session_'+generate_session_id()
            self.save()

            # Create a new container
            task = Task.objects.get(id=task_id)
            container = create_container(self.session_id, json.loads(task.initial_filesystem))

            # Set container ID
            self.container_id = container.id
            self.save()

            # Ask container to connect a WebSocket to this server
            requests.get('http://127.0.0.1:{}/{}/{}'.format(container.port, self.id, self.session_id))

            # Start current task
            task_result = self.get_current_task_result()
            if task_result.state == 'not_started':
                task_result.state = 'running'
                task_result.start_time = timezone.now()
                task_result.save()

            self.unlock()
            return self.session_id
        else: # Does not match current task
            self.unlock()
            return None

    def check_task_state(self, task_id: int) -> str:
        """Returns the state of the current TaskResult."""
        self.lock()
        state = TaskResult.objects.filter(task_manager_id=self.id).get(task_id=task_id).state
        self.unlock()
        return state

    def get_filesystem(self) -> Optional[dict]:
        """
        Returns a dictionary representation of the container's home directory,
        or None if there is no session running.
        """
        self.lock()
        if self.session_id == '':
            self.unlock()
            return None
        else:
            filesystem = disk_2_dict(pathlib.Path('/{}/home'.format(self.session_id)))['home']
            self.unlock()
            return filesystem

    def write_stdin(self, session_id: str, text: str) -> bool:
        """Write into the current session's STDIN channel.

        Does not perform write and returns False if session_id does not match
        self.session_id or if STDIN channel has not been registered yet.

        Used for testing only.
        """
        self.lock()
        if session_id == self.session_id and self.container_stdin_channel_name != '':
            Channel(self.container_stdin_channel_name).send({'text': text})
            self.unlock()
            return True
        else:
            self.unlock()
            return False

    def get_current_task_result(self) -> TaskResult:
        """Returns the current TaskResult object."""
        self.lock()
        task_result = TaskResult.objects.filter(task_manager_id=self.id).get(task_id=self.task_id)
        self.unlock()
        return task_result

    def update_state(self):
        """Updates the state of the current TaskResult."""

        self.lock()

        # Check if done with tasks
        if self.task_id == -1:
            self.unlock()
            return

        task_result = self.get_current_task_result()

        def commit_task_result_and_setup_next_task(state):
            # Commit task result
            task_result.state = state
            task_result.stdin = self.stdin
            task_result.stdout = self.stdout
            task_result.time_spent = timezone.now() - task_result.start_time
            task_result.save()

            # Destroy current container
            Container.objects.get(id=self.container_id).destroy()

            # Reset task manager fields
            self.stdin = ''
            self.stdout = ''
            self.session_id = ''
            self.container_id = -1
            self.container_stdin_channel_name = ''
            self.xterm_stdout_channel_name = ''
            self.save()

            # Advance to next task, or indicate that all tasks are finished
            if self.task_id == len(Task.objects.all()):
                self.task_id = -1
            else:
                self.task_id += 1
            self.save()

        if task_result.state == 'running':
            if timezone.now() > task_result.end_time():
                commit_task_result_and_setup_next_task('timed_out')
            else:
                # check answer
                task = Task.objects.get(id=self.task_id)
                if task.type == 'stdout':
                    if task.answer in self.stdout:
                        commit_task_result_and_setup_next_task('passed')
                elif task.type == 'filesystem':
                    container_filesystem = self.get_filesystem()
                    answer_filesystem = json.loads(task.answer)
                    if container_filesystem == answer_filesystem:
                        commit_task_result_and_setup_next_task('passed')
                else:
                    raise Exception('unrecognized task type')
        else:
            # No need to update if task is not running
            pass
        self.unlock()

def create_task_manager() -> TaskManager:
    """
    Create a TaskManager model.
    Retrieves Task's from the database to create TaskResult's.
    """

    tasks = Task.objects.all()
    if len(tasks) == 0:
        raise Exception('No tasks loaded')
    task_manager = TaskManager.objects.create(
        task_id=1,
        stdin='',
        stdout='',
        session_id='',
        container_id=-1,
        container_stdin_channel_name='',
        xterm_stdout_channel_name='',
    )
    # Create task results for each task
    for task in tasks:
        TaskResult.objects.create(
            task=task,
            task_manager=task_manager,
            stdin='',
            stdout='',
            start_time=timezone.now(), # this is just an arbitrary value to satisfy non-NULL constraint
            state='not_started',
            time_spent=datetime.timedelta(seconds=1), # arbitrary value to satisfy non-NULL constraint
        )
    return task_manager

class User(models.Model):
    """Describes a study participant."""

    """
    Code uniquely identifies a study participant.
    Participants will use this to log into the task interface.
    """
    access_code = models.TextField()

    """
    TaskManager that handles this User's tasks.
    """
    task_manager = models.OneToOneField('TaskManager', on_delete=models.CASCADE)

def create_user(access_code) -> User:
    """Create a User model."""
    task_manager = create_task_manager()
    return User.objects.create(access_code=access_code, task_manager=task_manager)
