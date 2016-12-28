"""
This file defines special model classes that are used to create and manipulate
SQL tables.

Create an SQL database with these model definitions by running:

python3 manage.py makemigrations website
python3 manage.py migrate
"""
from django.db import models
from django.utils import timezone
from .filesystem import dict_2_disk, disk_2_dict

import docker
import os
import time
import subprocess
import uuid
import fcntl
import datetime
import pathlib
import json
from typing import Optional


PART_I_TASKS = [1]
PART_II_TASKS = [2]

class User(models.Model):
    """
    Describes a study participant.

    :member access_code: Code which uniquely identifies a study participant.
        Participants will use this to log into the task interface.
    :member first_name: user's first name
    :member last_name: user's last name

    :member treatment_order: a user is 50/50 randomly assigned one of the
        following two treatment orders
        - Tellina / Google
        - Google / Tellina
    """
    access_code = models.TextField()
    first_name = models.TextField()
    last_name = models.TextField()
    treatment_order = models.TextField()

class Task(models.Model):
    """
    Describes a task used in the study.

    :member task_id: The ID that uniquely identifies a task. This makes the
        implementation of task scheduler easier.
    :member type: The type of task. Can be 'stdout' or 'filesystem'.
    :member description: A human-readable description of the task.
    :member initial_filesystem: JSON representation of the user's starting home
        directory
    :member goal: Goal stdout (if type is 'stdout') or JSON representation of
        the goal directory (if type is 'filesystem')
    :member duration: How much time is alotted for the task.
    """
    task_id = models.PositiveIntegerField()
    type = models.TextField()
    description = models.TextField()
    initial_filesystem = models.TextField()
    goal = models.TextField()
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


def create_container(filesystem_name, user_name):
    """
    Creates a container whose filesystem is located at /{filesystem_name}/home
    on the host. The contents of filesystem are written to
    /{filesystem_name}/home.
    """

    # Make virtual filesystem
    subprocess.run(['/bin/bash', 'make_filesystem.bash', filesystem_name])

    # Create Docker container
    # NOTE: the created container does not run yet
    cli = docker.Client(base_url='unix://var/run/docker.sock')
    docker_container = cli.create_container(
        image='backend_container',
        ports=[10411],
        volumes=['/home/' + user_name],
        host_config=cli.create_host_config(
            binds={
                '/{}/home'.format(filesystem_name): {
                    'bind': '/home/' + user_name,
                    'mode': 'rw',
                },
            },
            port_bindings={10411: ('0.0.0.0',)},
        ),
    )

    # Get ID of created container
    container_id = docker_container['Id']

    # Start container
    cli.start(container=container_id)

    # Set the permssions of the user's home directory.
    #
    # I tried to do this with the docker-py API and I couldn't get it to work,
    # so I'm just running a shell command.
    subprocess.run(['docker', 'exec', '-u', 'root', container_id,
        'chown', '-R', '{}:{}'.format(user_name, user_name),
        '/home/{}'.format(user_name)])

    # Find what port the container was mapped to
    info = cli.inspect_container(container_id)
    port = int(info['NetworkSettings']['Ports']['10411/tcp'][0]['HostPort'])

    # Wait a bit for container's server to start
    time.sleep(1)

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
    :member creation_time: Time the study session is created. Used for managing
        unexpectedly interrupted sessions.

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
    total_num_tasks = models.PositiveIntegerField(default=2)
    creation_time = models.DateTimeField()

    current_task_session_id = models.TextField()
    num_tasks_completed = models.PositiveIntegerField(default=0)
    status = models.TextField()


class TaskSession(models.Model):
    """
    A task performed by a user in a study session.

    :member study_session: The study session to which the task session belong.
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
    session_id = models.TextField(primary_key=True)
    task = models.ForeignKey(Task)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(default='1990-09-27 00:00:00')
    status = models.TextField()


class ActionHistory(models.Model):
    """
    An action history includes the operations done by the user at a specific
    time in a task session.

    :member task_session: The task session during which the action is taken.
    :member action: The action performed by the user, including
        - bash command issued by the user in the terminal
        - `quit` if the user quit the task
        - `reset` if the user resets the filesystem
    :member action_time: The time the action is taken.
    """
    task_session = models.ForeignKey(TaskSession, on_delete=models.CASCADE)
    action = models.TextField()
    action_time = models.DateTimeField()


class TaskScheduler(object):

    # Prefix to be used in naming lock files.
    LOCK_FILE_PREFIX = 'task_manager_lock_'
