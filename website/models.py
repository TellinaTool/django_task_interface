"""
This file defines special model classes that are used to create and manipulate
SQL tables.

Create an SQL database with these model definitions by running:

python3 manage.py makemigrations website
python3 manage.py migrate
"""

from django.db import models
from django.utils import timezone
from .constants import *

import docker
# import os
import time
import subprocess
# import uuid
# import fcntl
# import datetime
# import pathlib
# import json
# from typing import Optional

WEBSITE_DEVELOP = True

# unimplemented tasks: 3, 7, 8, 9, 10
TASK_BLOCK_I = [19,17,15,13,1,2,4,5]
TASK_BLOCK_II = [18,16,14,6,9,11,12]

treatment_A = 'Tellina or Google Search'
treatment_B = 'Google Search'

treatment_A_training_tasks = [1]
treatment_B_training_tasks = [2]

treatment_assignments = {
    'group1I': 'A',
    'group1II': 'B',
    'group2I': 'B',
    'group2II': 'A',
    'group3I': 'A',
    'group3II': 'B',
    'group4I': 'A',
    'group4II': 'B'
}

class User(models.Model):
    """
    Describes a study participant.

    :member access_code: Code which uniquely identifies a study participant.
        Participants will use this to log into the task interface.
    :member first_name: user's first name
    :member last_name: user's last name
    :member group: user's group assignment
        Group 1: task block 1 + Tellina / task block 2 + Google
        Group 2: task block 1 + Google / task block 2 + Tellina
        Group 3: task block 2 + Tellina / task block 1 + Google
        Group 4: task block 2 + Google / task block 1 + Tellina
    """
    access_code = models.TextField()
    first_name = models.TextField()
    last_name = models.TextField()
    group = models.TextField(default='group1')

class Task(models.Model):
    """
    Describes a task used in the study.

    :member task_id: The ID that uniquely identifies a task. This makes the
        implementation of task scheduler easier.
    :member type: The type of task. Can be 'stdout' or 'filesystem'.
    :member description: A precise description of the task.
    :member stdout: The expected standard output for the task. Empty if task
        type is not 'stdout'.
    :member file_attributes: File attributes used in the tasks.
    :member initial_filesystem: JSON representation of the user's starting home
        directory
    :member goal_filesystem: JSON representation of the goal directory (if type
        is 'filesystem')
    :member duration: How much time is alotted for the task.
    """
    task_id = models.PositiveIntegerField()
    type = models.TextField()
    description = models.TextField()
    stdout = models.TextField(default='')
    file_attributes = models.TextField()
    initial_filesystem = models.TextField()
    goal_filesystem = models.TextField()
    duration = models.DurationField()

# --- Container Management --- #

class Container(models.Model):
    """
    Describes information about a running Docker container.

    :member container_id: The ID of the container assigned by Docker.
    :member filesystem_name: The virtual filesystem that backs this container's
        home directory is located at /{filesystem_name}/home, which normally
        equals to the id of the study session the container is associated with.
    :member port: The host port through which the server in the container can
        be accessed.
    """
    container_id = models.TextField()
    filesystem_name = models.TextField()
    port = models.IntegerField()

    def destroy(self):
        """Destroys container, filesystem, and database entry."""

        # Destroy Docker container
        subprocess.run(['docker', 'rm', '-f', self.container_id])
        # Destroy filesystem
        subprocess.run(['/bin/bash', 'delete_filesystem.bash', self.filesystem_name])
        # Delete table entry
        # self.delete()

def create_container(filesystem_name):
    """
    Creates a container whose filesystem is located at /{filesystem_name}/home
    on the host. The contents of filesystem are written to
    /{filesystem_name}/home.
    """

    # Make virtual filesystem
    subprocess.run(['/bin/bash', 'make_filesystem.bash', filesystem_name, HOME])

    # Create Docker container
    # NOTE: the created container does not run yet
    client = docker.Client(base_url='unix://var/run/docker.sock')
    docker_container = client.create_container(
        image='backend_container',
        ports=[10411],
        volumes=['/home/' + USER_NAME],
        host_config=client.create_host_config(
            binds={
                '/{}/home'.format(filesystem_name): {
                    'bind': '/home/' + USER_NAME,
                    'mode': 'rw',
                },
            },
            port_bindings={10411: ('0.0.0.0',)},
        ),
    )

    # Get ID of created container
    container_id = docker_container['Id']

    # Start container and write standard output and error to a log file
    subprocess.run(
        args='docker start -a {} >container_{}.log 2>&1 &'.format(container_id, container_id),
        shell=True,
        executable='/bin/bash',
    )

    # Wait a bit for container's to start
    time.sleep(1)

    # Set the permissions of the user's home directory.
    #
    # I tried to do this with the docker-py API and I couldn't get it to work,
    # so I'm just running a shell command.
    subprocess.call(['docker', 'exec', '-u', 'root', container_id,
        'chown', '-R', '{}:{}'.format(USER_NAME, USER_NAME),
        '/home/{}'.format(USER_NAME)])

    # Find what port the container was mapped to
    info = client.inspect_container(container_id)
    port = int(info['NetworkSettings']['Ports']['10411/tcp'][0]['HostPort'])

    # Create container model object
    container = Container.objects.create(
        container_id=container_id,
        filesystem_name=filesystem_name,
        port=port,
    )

    return container


class StudySession(models.Model):
    """
    A study session participated by a user.

    :member user: The participant of the session.
    :member session_id: an application-wide unique study session ID.
    :member container: The Container model associated with the session. None if
        no container is associated.
    :member total_num_tasks: Total number of tasks in the study session.
    :member creation_time: Time the study session is created.
    :member close_time: Time the study session is closed.

    :member current_task_session_id: The id of the task session that the user
        is undertaking. '' if no task session is running.
    :member num_tasks_completed: The number of tasks that has been completed in
        the study session.
    :member status: The state of the study session.
        - 'finished': The user has completed the study session.
        - 'closed_with_error': The session is closed due to exceptions.
        - 'paused': The user left the study session in the middle. Paused
            study sessions can be resumed.
        - 'running': The user is currently taking the study session.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.TextField(primary_key=True)
    container = models.ForeignKey(Container, default=None)
    total_num_tasks = models.PositiveIntegerField(default=
        len(TASK_BLOCK_I) + len(TASK_BLOCK_II))
    creation_time = models.DateTimeField(default='')
    end_time = models.DateTimeField(default='1111-11-11 00:00:00')

    current_task_session_id = models.TextField()
    num_tasks_completed = models.PositiveIntegerField(default=0)
    status = models.TextField()

    def create_new_container(self):
        self.container = create_container(self.session_id)
        self.save()

    def close(self, reason_for_close):
        # ignore already closed study sessions
        if self.status == 'running' or self.status == 'paused':
            self.current_task_session_id = ''
            self.close_time = timezone.now()
            self.status = reason_for_close
            self.save()

            # destroy the container associated with the study session
            self.container.destroy()

    def get_part(self):
        # compute which
        if not WEBSITE_DEVELOP:
            assert(len(TASK_BLOCK_I) == len(TASK_BLOCK_II))
        if self.user.group in ['group1', 'group4']:
            part1_tasks = TASK_BLOCK_I
        else:
            part1_tasks = TASK_BLOCK_II
        if self.num_tasks_completed < len(part1_tasks):
            return 'I'
        else:
            return 'II'

    def inc_num_tasks_completed(self):
        self.num_tasks_completed += 1
        self.save()

    def update_current_task_session_id(self):
        new_task_session_id = self.session_id + \
               '/task-{}'.format(self.num_tasks_completed + 1)
        self.current_task_session_id = new_task_session_id
        self.save()
        return new_task_session_id


class TaskSession(models.Model):
    """
    A task performed by a user in a study session.

    :member study_session: The study session to which the task session belong.
    :member study_session_part: The part of the study session the task session
        is in.
    :member session_id: an application-wide unique task session ID.
    :member task: The task being performed in the task session.
    :member start_time: The start time of a task session.
    :member end_time: The end time of a task session. None if the task session
        is being undertaken.
    :member status: The state of the task result.
        - 'running':     The user has started the task, but the task has not
                         passed nor timed out yet
        - 'time_out':   The user started the task and did not pass it before
                         running out of time
        - 'quit':        The user quit the task
        - 'passed':      The user started the task and passed it
    """
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE)
    study_session_part = models.TextField()
    session_id = models.TextField(primary_key=True)
    task = models.ForeignKey(Task)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(default='1111-11-11 00:00:00')
    status = models.TextField()

    def close(self, reason_for_close):
        self.end_time = timezone.now()
        self.study_session.container.destroy()
        self.status = reason_for_close
        self.save()

    def get_treatment(self):
        user = self.study_session.user
        return treatment_assignments[user.group + self.study_session_part]


class ActionHistory(models.Model):
    """
    An action history includes the operations done by the user at a specific
    time in a task session.

    :member task_session: The task session during which the action is taken.
    :member action: The action performed by the user, including
        - bash command issued by the user in the terminal
        - `__reset__` if the user resets the filesystem
    :member action_time: The time the action is taken.
    """
    task_session = models.ForeignKey(TaskSession, on_delete=models.CASCADE)
    action = models.TextField()
    action_time = models.DateTimeField()
