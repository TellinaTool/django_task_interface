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
    filesystem_name = models.TextField()
    container_id = models.TextField()
    port = models.IntegerField()

    def destroy(self):
        # Destroy Docker container
        subprocess.run(['docker', 'rm', '-f', self.container_id])
        # Destroy filesystem
        subprocess.run(['/bin/bash', 'delete_filesystem.bash', self.filesystem_name])
        # Delete table entry
        self.delete()

def create_container(filesystem_name: str, filesystem: dict) -> Container:
    # Make  virtual filesystem
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

    # Inspect created container
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
    type = models.TextField()
    description = models.TextField()
    initial_filesystem = models.TextField()
    answer = models.TextField()
    duration = models.DurationField()

    def to_dict(self) -> dict:
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
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    task_manager = models.ForeignKey('TaskManager', on_delete=models.CASCADE)
    stdin = models.TextField()
    stdout = models.TextField()
    start_time = models.DateTimeField()
    state = models.TextField() # 'not_started' | 'running' | 'timed_out' | 'passed'
    time_spent = models.DurationField()

    def end_time(self) -> datetime.datetime:
        return self.start_time + self.task.duration

class SessionID(models.Model):
    pass

def generate_session_id() -> str:
    session_id = SessionID.objects.create()
    return str(session_id.id)

class TaskManager(models.Model):
    '''
    Invariant: 0 or 1 container running at a time.
    Instantiates task_manager_{id}.lock to serialize requests.
    Uses 'session_id' to keep track of websocket sessions.
    Depends on code in consumers.py to register websockets.

    Container should connect on /container/{task_manager.id}/{task_manager.session_id}
    User should connect on /xterm/{task_manager.id}/{task_manager.session_id}
    '''

    # Current task
    # -1 means that all tasks are done
    task_id = models.IntegerField()

    # These are saved to TaskResult and reset here when a task is finished
    stdin = models.TextField()
    stdout = models.TextField()

    # The following fields are associated with a session:
    session_id = models.TextField()                   # '' means no session currently
    container_id = models.IntegerField()              # -1 means no container
    container_stdin_channel_name = models.TextField() # '' means websocket not connected yet
    xterm_stdout_channel_name = models.TextField()    # '' means websocket not connected yet

    def lock(self):
        with open('task_manager_lock_{}'.format(self.id), 'w+') as file:
            fcntl.flock(file, fcntl.LOCK_EX)
        self.refresh_from_db()

    def unlock(self):
        with open('task_manager_lock_{}'.format(self.id), 'w+') as file:
            fcntl.flock(file, fcntl.LOCK_UN)

    def get_current_task_id(self) -> int:
        self.lock()
        task_id = self.task_id
        self.unlock()
        return task_id

    # Handles starting new task, opening new window to current
    # task, resetting current task
    # Returns None if task_id does not match self.task_id
    def initialize_task(self, task_id: int) -> Optional[str]:
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
        self.lock()
        state = TaskResult.objects.filter(task_manager_id=self.id).get(task_id=task_id).state
        self.unlock()
        return state

    def get_filesystem(self) -> Optional[dict]:
        self.lock()
        if self.session_id == '':
            self.unlock()
            return None
        else:
            filesystem = disk_2_dict(pathlib.Path('/{}/home'.format(self.session_id)))['home']
            self.unlock()
            return filesystem

    # Used for testing only
    def write_stdin(self, session_id: str, text: str) -> bool:
        self.lock()
        if session_id == self.session_id and self.container_stdin_channel_name != '':
            Channel(self.container_stdin_channel_name).send({'text': text})
            self.unlock()
            return True
        else:
            self.unlock()
            return False

    def get_current_task_result(self) -> TaskResult:
        self.lock()
        task_result = TaskResult.objects.filter(task_manager_id=self.id).get(task_id=self.task_id)
        self.unlock()
        return task_result

    def update_state(self):
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
    access_code = models.TextField()
    task_manager = models.OneToOneField('TaskManager', on_delete=models.CASCADE)

def create_user(access_code) -> User:
    task_manager = create_task_manager()
    return User.objects.create(access_code=access_code, task_manager=task_manager)
