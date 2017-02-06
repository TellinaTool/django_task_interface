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
import os
import subprocess
import time

WEBSITE_DEVELOP = True

# unimplemented tasks: 3, 20
TASK_TRAINING = [21, 22]
TASK_BLOCK_I = [13, 4, 7, 11, 5, 9, 17, 10, 18]
TASK_BLOCK_II = [15, 1, 6, 8, 12, 19, 2, 14, 16]

if not WEBSITE_DEVELOP:
    assert(len(TASK_BLOCK_I) == len(TASK_BLOCK_II))

# key: treatment order + study session stage
# value: treatment
treatment_assignments = {
    '0I': 'A',
    '0II': 'B',
    '1I': 'B',
    '1II': 'A'
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
    :member type: The type of task. Can be 'stdout', 'file_search' or
        'filesystem_change'.
    :member description: A precise description of the task.
    :member file_attributes: File attributes used in the tasks.
    :member initial_filesystem: JSON representation of the user's starting home
        directory
    :member goal_filesystem: JSON representation of the goal directory (if type
        is 'filesystem_change')
    :member stdout: The expected standard output for the task. Empty if task
        type is not 'stdout'.
    :member duration: How much time is alotted for the task.
    :member solution (for training purpose): A bash one-liner that solves the
        task (a task usually have more than one solutions).
    """
    task_id = models.PositiveIntegerField()
    type = models.TextField()
    description = models.TextField()
    file_attributes = models.TextField()
    initial_filesystem = models.TextField(default='')
    goal_filesystem = models.TextField(default='')
    stdout = models.TextField(default='')
    duration = models.DurationField()
    solution = models.TextField(default='')

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
        subprocess.run(['/bin/bash', 'delete_filesystem.bash',
                        self.filesystem_name])
        # Delete table entry
        # self.delete()

def create_container(filesystem_name, task):
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
        args='docker start -a {} >container_{}.log 2>&1 &'
            .format(container_id, container_id),
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

    # Change file parameters according to the task specification if necessary
    if task.task_id == 3:
        # TODO: to read the owner of a file correctly, the disk_2_dict function
        # needs to read from the docker container instead of the virtual file
        # system
        subprocess.call(['docker', 'exec', '-u', 'root', container_id,
                         'adduser', USER_NAME, 'sudo'])
        # subprocess.call(['docker', 'exec', '-u', 'root', container_id, 'bash',
        # '-c', '\'echo "me ALL = (ALL) NOPASSWD: ALL" > /etc/sudoers\''])
        subprocess.call(['docker', 'exec', '-u', 'root', container_id,
                         'useradd', '-m', USER2_NAME])
    elif task.task_id == 7:
        filesystem_vfs_path = '/{}/home/website/'.format(filesystem_name)
        os.utime(filesystem_vfs_path + 'css/bootstrap3/bootstrap-glyphicons.css',
                 (1454065722, 1454065722))
        os.utime(filesystem_vfs_path + 'css/fonts/glyphiconshalflings-regular.eot',
                 (1454065722, 1454065722))
        os.utime(filesystem_vfs_path + 'css/fonts/glyphiconshalflings-regular.otf',
                 (1454065722, 1454065722))
        os.utime(filesystem_vfs_path + 'css/fonts/glyphiconshalflings-regular.svg',
                 (1454065722, 1454065722))
        os.utime(filesystem_vfs_path + 'css/fonts/glyphiconshalflings-regular.ttf',
                 (1454065722, 1454065722))
    elif task.task_id == 8:
        filesystem_vfs_path = '/{}/home/website/'.format(filesystem_name)
        os.utime(filesystem_vfs_path + 'content/labs/2013/10.md',
                 (1454065722, 1454065722))
        os.utime(filesystem_vfs_path + 'content/labs/2013/12.md',
                 (1454065722, 1454065722))

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
    :member creation_time: Time the study session is created.
    :member close_time: Time the study session is closed.
    :member half_session_time_left: Time left in the current half of the study
        session.

    :member current_task_session_id: The id of the task session that the user
        is undertaking. '' if no task session is running.
    :member total_num_training_tasks: Total number of training tasks in the
        study session.
    :member total_num_tasks: Total number of tasks in the study session.
    :member num_training_tasks_completed: The number of training tasks that has
        been completed in the study session.
    :member num_tasks_completed: The number of tasks that has been completed in
        the study session.

    :member status: The state of the study session.
        - 'finished': The user has completed the study session.
        - 'closed_with_error': The session is closed due to exceptions.
        - 'paused': The user left the study session in the middle. Paused
            study sessions can be resumed.
        - 'reading_consent': The user is reading but has not signed the consent form.
        - 'reading_instructions': The user is reading the instructions but has
            not started the study session.
        - 'running': The user is taking the study session.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.TextField(primary_key=True)

    creation_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    half_session_time_left = models.DurationField(null=True, blank=True)

    current_task_session_id = models.TextField(default='')
    total_num_training_tasks = models.PositiveIntegerField(
        default=len(TASK_TRAINING))
    total_num_tasks = models.PositiveIntegerField(
        default=len(TASK_BLOCK_I) + len(TASK_BLOCK_II))
    num_training_tasks_completed = models.PositiveIntegerField(default=0)
    num_tasks_completed = models.PositiveIntegerField(default=0)

    # filesystem_change_seen = models.BooleanField(default=False)
    # file_search_seen = models.BooleanField(default=False)
    # standard_output_seen = models.BooleanField(default=False)
    status = models.TextField(default='reading_consent')

    def close(self, reason_for_close):
        # ignore already closed study sessions
        if self.status == 'running' or self.status == 'paused':
            self.current_task_session_id = ''
            self.close_time = timezone.now()
            self.status = reason_for_close
            self.save()

    def closed(self):
        return self.status in ['finished', 'closed_with_error', 'paused']

    # --- Task manager --- #

    def inc_num_tasks_completed(self):
        if self.half_session_time_left <= timezone.timedelta(seconds=0):
            # force stage change
            if self.stage == 'I':
                self.num_tasks_completed = self.switch_point
            elif self.stage == 'II':
                self.num_tasks_completed = self.total_num_tasks
        else:
            self.num_tasks_completed += 1
        self.save()

    def inc_num_training_tasks_completed(self):
        self.num_training_tasks_completed += 1
        self.save()

    def start_half_session_timer(self):
        self.half_session_time_left = timezone.timedelta(
            minutes=half_session_length)
        self.save()

    def update_half_session_time_left(self, time_spent):
        self.half_session_time_left -= time_spent
        print('half_session_time_left: {}'.format(self.half_session_time_left))
        self.save()

    def update_current_task_session_id(self):
        """
        Task scheduling function.
        """
        if self.num_training_tasks_completed == 0 and \
                        self.num_tasks_completed == 0:
            new_task_session_id = self.session_id + \
                '-training-task-{}'.format(self.num_training_tasks_completed + 1)
        elif self.num_training_tasks_completed == 1 and \
                self.num_tasks_completed == self.switch_point:
            new_task_session_id = self.session_id + \
                '-training-task-{}'.format(self.num_training_tasks_completed + 1)
        else:
            new_task_session_id = self.session_id + \
                '-task-{}'.format(self.num_tasks_completed + 1)
        self.current_task_session_id = new_task_session_id
        self.save()
        return new_task_session_id

    def stage_change(self):
        # check if the study session is going through a stage change
        if self.num_training_tasks_completed == 0 and \
                self.num_tasks_completed == 0:
            # entering stage I
            print('entering stage I')
            return True
        elif self.num_training_tasks_completed == 1 and \
                self.num_tasks_completed == self.switch_point:
            # entering stage II
            print('entering stage II')
            return True
        elif self.num_training_tasks_completed == 2 and \
                self.num_tasks_completed == self.total_num_tasks:
            # entering stage III
            print('entering stage III')
            return True
        return False

    @property
    def stage(self):
        # compute which stage of the study the user is currently at
        assert(self.num_tasks_completed <= self.total_num_tasks)

        if self.status in ['reading_consent', 'reading_instructions']:
            return 'O'
        elif self.status == 'running':
            if self.num_tasks_completed < self.switch_point:
                return 'I'
            elif self.num_tasks_completed < self.total_num_tasks:
                return 'II'
            else:
                return 'III'
        else:
            raise ValueError('Wrong study session status: "{}" while checking '
                             'current study session stage'.format(self.status))

    @property
    def switch_point(self):
        # number of tasks in the first part of the study
        if self.user.group in ['group1', 'group4']:
            return len(TASK_BLOCK_I)
        else:
            return len(TASK_BLOCK_II)

    @property
    def task_block_order(self):
        # the task block order of the study session
        if self.user.group in ['group1', 'group4']:
            return '0'
        else:
            return '1'

    @property
    def treatment_order(self):
        # the treatment order of the study session
        if self.user.group in ['group1', 'group3']:
            return '0'
        else:
            return '1'

    @property
    def treatment(self):
        # the treatment being used in the current half of the study
        return treatment_assignments[self.treatment_order + self.stage]


class TaskSession(models.Model):
    """
    A task performed by a user in a study session.

    :member study_session: The study session to which the task session belong.
    :member study_session_stage: The part of the study session the task session
        is in.
    :member session_id: an application-wide unique task session ID.
    :member container: The Container model associated with the task session.
        None if no container is associated.
    :member is_training: Set to true if the task session is for training
        purpose.
    :member task: The task being performed in the task session.

    :member start_time: The start time of a task session.
    :member end_time: The end time of a task session. None if the task session
        is being undertaken.
    :member time_left: Time left in this task session. This is used for
        redirecting the user when a half session timed out.

    :member status: The state of the task result.
        - 'running':     The user has started the task, but the task has not
                         passed nor timed out yet
        - 'time_out':   The user started the task and did not pass it before
                         running out of time
        - 'quit':        The user quit the task
        - 'passed':      The user started the task and passed it
    """
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE)
    study_session_stage = models.TextField()
    session_id = models.TextField(primary_key=True)
    container = models.ForeignKey(Container, default=None)
    is_training = models.BooleanField(default=False)
    task = models.ForeignKey(Task)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_left = models.DurationField(null=True, blank=True)

    status = models.TextField()

    def close(self, reason_for_close):
        self.status = reason_for_close
        self.end_time = timezone.now()
        if not self.is_training:
            time_spent = self.get_time_spent_since_last_resume(self.end_time)
            self.update_time_left(time_spent)
            self.study_session.update_half_session_time_left(time_spent)
        self.container.destroy()
        self.save()

    def create_new_container(self):
        if self.container:
            # make sure any existing container is destroyed
            self.destroy_container()
        self.container = create_container(self.session_id, self.task)
        self.save()

    def destroy_container(self):
        self.container.destroy()
        self.container = None

    def get_action_history(self):
        # the user's action history in the task session ordered from the
        # least recent to the most recent
        return ActionHistory.objects.filter(task_session=self)\
            .order_by('action_time')

    def get_time_spent_since_last_resume(self, current_time):
        # compute time spent since last time update
        if ActionHistory.objects.filter(task_session=self,
                                        action='__resumed__').exists():
            most_recent_resume = self.get_action_history\
                .filter(action='__resumed__').order_by('action_time')[-1]
            return current_time - most_recent_resume.action_time
        else:
            return current_time - self.start_time

    def set_time_left(self, time_left):
        self.time_left = time_left
        self.save()

    def set_start_time(self, start_time):
        self.start_time = start_time
        self.save()

    def update_time_left(self, time_spent):
        self.time_left -= time_spent
        self.save()

    @property
    def time_spent(self):
        time_spent = timezone.timedelta(seconds=0)
        last_resumed_time = self.start_time
        action_history = self.get_action_history()
        for action in action_history:
            if action.action == '__paused__':
                time_spent += (action.action_time - last_resumed_time)
            if action.action == '__resumed__':
                last_resumed_time = action.action_time
        if self.status == 'passed':
            # get the timestamp of the command that solves the task
            assert(action_history)
            last_action = action_history[len(action_history)-1]
            time_spent += last_action.action_time - last_resumed_time
        else:
            time_spent += self.end_time - last_resumed_time
        return time_spent


class ActionHistory(models.Model):
    """
    An action history includes the operations done by the user at a specific
    time in a task session.get

    :member task_session: The task session during which the action is taken.
    :member action: The action performed by the user, including
        - bash command issued by the user in the terminal
        - `__reset__` if the user resets the filesystem
        - `__paused__` if the user paused the task session or the task session
            is interrupted
        - `__resumed__` if a paused task session is resumed
    :member action_time: The time the action is taken.
    """
    task_session = models.ForeignKey(TaskSession, on_delete=models.CASCADE)
    action = models.TextField()
    action_time = models.DateTimeField()

# --- Peripheral Data --- #

class Researcher(models.Model):
    """
    :member first name: researcher's first name
    :member last name: researcher's last name
    :member email: researcher's email address
    """
    first_name = models.TextField()
    last_name = models.TextField()
    email = models.TextField()


class Software(models.Model):
    """
    :member name: name of the software
    :member url: url of the software
    """
    name = models.TextField()
    url = models.TextField()