"""
This file defines functions to handle requests at URLs defined in urls.py.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .filesystem import *

from . import functions
import json
import pathlib
import re
import tarfile

def json_response(d={}, status='SUCCESS'):
    d.update({'status': status})
    resp = JsonResponse(d)
    return resp

def session_id_required(f):
    @functions.wraps(f)
    def g(request, *args, **kwargs):
        session_id = request.COOKIES['session_id']
        try:
            study_session = StudySession.objects.get(session_id=session_id)
            return f(request, *args, study_session=study_session, **kwargs)
        except ObjectDoesNotExist:
            return json_response(status='STUDY_SESSION_DOES_NOT_EXIST')
    return g

def task_session_id_required(f):
    @functions.wraps(f)
    def g(request, *args, **kwargs):
        session_id = request.COOKIES['session_id']
        task_session_id = request.COOKIES['task_session_id']
        # ensure that the task session id matches with the study session id
        if not task_session_id.startswith(session_id):
            return json_response(
                status='STUDY_SESSION_AND_TASK_SESSION_MISMATCH')
        try:
            task_session = TaskSession.objects.get(session_id=task_session_id)
            return f(request, *args, task_session=task_session, **kwargs)
        except ObjectDoesNotExist:
            return json_response(status='TASK_SESSION_DOES_NOT_EXIST')
    return g

# --- Task Management --- #

@task_session_id_required
def get_current_task(request, task_session):
    """
    Args:
        task_session

    Returns the information of the currently task in the user's study session.
    """
    task = task_session.task

    study_session = task_session.study_session
    task_part = task_session.study_session.get_part()

    order_number = study_session.num_tasks_completed + 1

    is_training = study_session.status == 'training'
    if is_training:
        context = {
            "is_training": is_training,
            "task_part": 'Training',
            "task_description": task.description,
            "task_order_number": 1,
            "total_num_tasks": 1,
            "first_name": study_session.user.first_name,
            "last_name": study_session.user.last_name,
        }
    else:
        context = {
            "is_training": is_training,
            "task_part": 'Part {}'.format(task_part),
            "task_description": task.description,
            "task_order_number": order_number,
            "total_num_tasks": study_session.total_num_tasks,
            "first_name": study_session.user.first_name,
            "last_name": study_session.user.last_name,
        }

    template = loader.get_template('task.html')
    return HttpResponse(template.render(context, request))

@task_session_id_required
def get_additional_task_info(request, task_session):
    """

    Args:
        task_session:

    Returns additional the maximum time length the user is allowed to spend on
    the task.

    """
    task = task_session.task
    container = task_session.container
    container_port = container.port

    # with open('fs-7-8.json', 'w') as o_f:
    #     json.dump(disk_2_dict(
    #       pathlib.Path('/{}/home/website'.format(container.filesystem_name)),
    #         [filesystem._MTIME]), o_f)

    fs_diff = compute_filesystem_diff(container, task, [],
                                      save_initial_filesystem=True)
    if fs_diff:
        filesystem_status = "FILE_SYSTEM_WRITTEN_TO_DISK"
    else:
        filesystem_status = "FILE_SYSTEM_ERROR"

    if task.type == "stdout":
        stdout_diff = compute_stdout_diff('', task)
        resp = {
            'filesystem_status': filesystem_status,
            'filesystem_diff': fs_diff,
            'stdout_diff': stdout_diff,
            'task_duration': task.duration.seconds,
            'page_tour': task_session.get_page_tour(),
            'container_port': container_port
        }
    else:
        resp = {
            'filesystem_status': filesystem_status,
            'filesystem_diff': fs_diff,
            'task_duration': task.duration.seconds,
            'page_tour': task_session.get_page_tour(),
            'container_port': container_port
        }

    return json_response(resp)

@task_session_id_required
def go_to_next_task(request, task_session):
    """
    Args:

        task_session:

    Create a new task session.
    """

    study_session = task_session.study_session

    # if a task session has ended, ignore requests for updating task attributes
    if task_session.status == 'running':
        # close current_task_session
        task_session.close(request.GET['reason_for_close'])
        # update relevant study session attributes
        if study_session.status == 'training':
            study_session.status = 'running'
        else:
            study_session.inc_num_tasks_completed()

    # check for user study completion
    num_tasks_completed = study_session.num_tasks_completed
    assert(num_tasks_completed <= study_session.total_num_tasks)
    if num_tasks_completed == study_session.total_num_tasks:
        study_session.close('finished')
        resp = json_response(
            {
                "num_passed": TaskSession.objects.filter(
                    study_session=study_session, status='passed').count(),
                "num_given_up": TaskSession.objects.filter(
                    study_session=study_session, status='quit').count(),
                "num_total": study_session.total_num_tasks
            },
            status='STUDY_SESSION_COMPLETE')
        resp.set_cookie('session_id', '')
        resp.set_cookie('task_session_id', '')
    else:
        next_task_session_id = study_session.update_current_task_session_id()
        create_task_session(study_session)
        if study_session.switch_part():
            status = 'SWITCH_PART'
        else:
            status = 'RUNNING'
        resp = json_response({"task_session_id": next_task_session_id},
                             status=status)
        resp.set_cookie('task_session_id', next_task_session_id)

    return resp

def create_task_session(study_session):
    """
    Pick a task from the database and initialize a new task session
    for the user.
    """
    user = study_session.user
    study_session_part = study_session.get_part()
    task_session_id = study_session.current_task_session_id
    is_training = (study_session.status == 'training')

    if not TaskSession.objects.filter(session_id=task_session_id).exists():
        if is_training:
            task_id = TASK_TRAINING[0]
        else:
            if user.group in ['group1', 'group4']:
                part1_tasks = TASK_BLOCK_I
                part2_tasks = TASK_BLOCK_II
            else:
                part1_tasks = TASK_BLOCK_II
                part2_tasks = TASK_BLOCK_I

            if study_session_part == 'I':
                task_id = part1_tasks[study_session.num_tasks_completed]
            else:
                task_id = part2_tasks[study_session.num_tasks_completed
                                      - len(part1_tasks)]

        # create the container of the task session
        task = Task.objects.get(task_id=task_id)
        container = create_container(task_session_id, task)

        TaskSession.objects.create(
            study_session = study_session,
            study_session_part = study_session.get_part(),
            session_id = task_session_id,
            container = container,
            is_training = is_training,
            task = task,
            start_time = timezone.now(),
            status = 'running'
        )
        print('Log: {} created'.format(task_session_id))

# --- Terminal I/O --- #

@task_session_id_required
@csrf_exempt
def on_command_execution(request, task_session):
    """
    Args:
        task_session:

    Record user's terminal standard output upon command execution. Check for
    task completion.
    """
    task = task_session.task
    stdout = request.POST['stdout']

    ActionHistory.objects.create(
        task_session=task_session,
        action = stdout,
        action_time = timezone.now()
    )

    # check if there are file path in the stdout
    stdout_lines = stdout.split('\n')
    current_dir = stdout_lines[-1][16:-2]
    stdout_paths = []
    for stdout_line in stdout_lines[1:-1]:
        path = extract_path(stdout_line, current_dir)
        if path:
            stdout_paths.append(path)

    # compute distance between current file system and the goal file system
    container = task_session.container

    fs_diff = compute_filesystem_diff(container, task, stdout_paths)
    if fs_diff is None:
        return json_response(status='FILE_SYSTEM_ERROR')

    task_completed = False
    if task.type == 'stdout':
        stdout_diff = compute_stdout_diff('\n'.join(stdout_lines[1:-1]), task,
                                          current_dir)
        # check if stdout signals task completion
        # the files/directories being checked must be presented in full paths
        # the file/directory names cannot contain spaces
        if stdout_diff['tag'] == 'correct':
            task_completed = True
        resp = { 'filesystem_diff': fs_diff, 'stdout_diff': stdout_diff }
    elif task.type == 'file_search' or task.type == 'filesystem_change':
        # check if the current file system is the same as the goal file system
        if not fs_diff['tag']:
            task_completed = True
        resp = { 'filesystem_diff': fs_diff }
    else:
        raise AttributeError('Unrecognized task type "{}": must be "stdout",'
            '"file_search" or "filesystem_change"'.format(task.type))

    if task_completed:
        return json_response(resp, status= 'TASK_COMPLETED')
    else:
        return json_response(resp)

# --- File System Management --- #

@task_session_id_required
def reset_file_system(request, task_session):
    """
    Args:
        task_session:

    Reset the file system of the current task session.
    """
    task = task_session.task

    # destroy the current container and create a new one
    task_session.create_new_container()
    container = task_session.container
    container_id = container.container_id

    ActionHistory.objects.create(
        task_session=task_session,
        action = '__reset__',
        action_time = timezone.now()
    )

    fs_diff = compute_filesystem_diff(container, task, [])
    if fs_diff is None:
        filesystem_status = 'FILE_SYSTEM_ERROR'
    else:
        filesystem_status = 'FILE_SYSTEM_WRITTEN_TO_DISK'

    if task.type == 'stdout':
        stdout_diff = compute_stdout_diff('', task)
        resp = {
            'container_id': container_id,
            'container_port': container.port,
            'filesystem_diff': fs_diff,
            'filesystem_status': filesystem_status,
            'stdout_diff': stdout_diff
        }
    else:
        resp = {
            'container_id': container_id,
            'container_port': container.port,
            'filesystem_diff': fs_diff,
            'filesystem_status': filesystem_status
        }
    
    return json_response(resp)

def compute_filesystem_diff(container, task, stdout_paths,
                            save_initial_filesystem=False):
    """
    Compute the difference between the current file system on disk and the goal
    file system. Return None if the current file system does not exist.

    Args:
        container: the container object on which the file system is mounted
        task: the task object which contains the definition of the file system
        stdout_paths: the paths detected from the user's terminal standard
            output which shall be annotated on the diff object
        save_initial_filesystem: set to True if the current file system on disk
            should be saved to the Task object

    """
    filesystem_vfs_path = '/{}/home/website'.format(container.filesystem_name)
    current_filesystem = disk_2_dict( pathlib.Path(filesystem_vfs_path),
            json.loads(task.file_attributes))
    if save_initial_filesystem:
        task.initial_filesystem = json.dumps(current_filesystem)
        task.save()

    if current_filesystem is None:
        return None

    goal_filesystem = task.initial_filesystem if task.type == 'stdout' \
        else task.goal_filesystem
    fs_diff = filesystem_diff(current_filesystem, json.loads(goal_filesystem))
    # annotate the fs_diff with the stdout_paths
    annotate_path_selection(fs_diff, task.type, stdout_paths)

    if not contains_error_in_child(fs_diff) and task.task_id == 2:
        files_in_tar = set()
        try:
            tar = tarfile.open(os.path.join(filesystem_vfs_path, 'html.tar'))
            for member in tar.getmembers():
                files_in_tar.add(os.path.basename(member.name))
        except tarfile.ReadError:
            # valid tar file does not exist on the target path
            pass
        if files_in_tar != {'index.html', 'home.html', 'labs.html',
                            'lesson.html', 'menu.html', 'navigation.html'}:
            annotate_node(fs_diff, pathlib.Path('website/html.tar'),
                          'incorrect')
    return fs_diff

def compute_stdout_diff(stdout, task, current_dir=None):
    """

    Args:
        stdout:
        task:
        current_dir:
        unordered:

    """
    def __equal__(l1, l2, task_id):
        if task_id == 16:
            # loose comparison is enough for tasks that requires date/time
            # to be outputed in a specific format
            path1 = extract_path(l1, current_dir)
            path2 = extract_path(l2, '~/website')
            if path1 == path2:
                time_long_iso_re = re.compile(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}'
                                             r'(:\d{2}(\.\d+)?)?')
                if re.search(time_long_iso_re, l1):
                    return True
        elif task_id == 19:
            # loose comparison is enough for tasks that requires the number of
            # lines in a file
            num_of_lines, _ = l2.split()
            num_of_lines_pattern = re.compile(r'{}\s'.format(num_of_lines))
            path1 = extract_path(l1, current_dir)
            path2 = extract_path(l2, '~/website')
            if path1 == path2 and (re.search(num_of_lines_pattern, l1)):
                return True
        else:
            return l1 == l2
        return False

    stdout1 = [line.strip() for line in stdout.split('\n') if line]
    stdout2 = [line.strip() for line in task.stdout.split('\n')]

    stdout_diff = []
    tag = 'correct'

    if task.task_id != 10:
        # boolean variable which is used decide if the "total line" should be
        # shown as correct or as an error
        unmatch_detected = False
        matched_stdout2 = []
        for l1 in stdout1:
            if not l1:
                continue
            matched = False
            for i in range(len(stdout2)):
                if not i in matched_stdout2 and \
                        __equal__(l1, stdout2[i], task.task_id):
                    matched = True
                    matched_stdout2.append(i)
                    break
            if matched:
                stdout_diff.append({
                    'line': l1,
                    'tag': 'correct'
                })
            else:
                total_pattern = re.compile(r'(total\s|\stotal)')
                if not unmatch_detected and \
                        (task.task_id == 19 and re.search(total_pattern, l1)):
                    stdout_diff.append({
                        'line': l1,
                        'tag': 'correct'
                    })
                else:
                    stdout_diff.append({
                        'line': l1,
                        'tag': 'extra'
                    })
                    tag = 'incorrect'
        for i in range(len(stdout2)):
            if not i in matched_stdout2:
                l2 = stdout2[i]
                stdout_diff.append({
                    'line': l2,
                    'tag': 'missing'
                })
                tag = 'incorrect'
    else:
        i = 0
        j = 0
        while i < len(stdout1) and j < len(stdout2):
            l1 = stdout1[i]
            l2 = stdout2[j]
            path1 = extract_path(l1, current_dir)
            path2 = extract_path(l2, current_dir)

            if path1 and path1 == path2:
                stdout_diff.append({
                    'line': l1,
                    'tag': 'correct'
                })
                i += 1
                j += 1
            else:
                if path1 is None or path1.name < path2.name:
                    stdout_diff.append({
                        'line': l1,
                        'tag': 'extra'
                    })
                    tag = 'incorrect'
                    i += 1
                else:
                    stdout_diff.append({
                        'line': l2,
                        'tag': 'missing'
                    })
                    tag = 'incorrect'
                    j += 1
        if i < len(stdout1):
            for l1 in stdout1[i:]:
                stdout_diff.append({
                    'line': l1,
                    'tag': 'extra'
                })
            tag = 'incorrect'
        if j < len(stdout2):
            for l2 in stdout2[j:]:
                stdout_diff.append({
                    'line': l2,
                    'tag': 'missing'
                })
            tag = 'incorrect'

    return { 'lines': stdout_diff, 'tag': tag }

# --- Progress Indicator --- #
@session_id_required
def progress(request, study_session):
    template = loader.get_template('progress.html')
    context = {
        'step': study_session.get_part(),
        'treatment': study_session.get_treatment(),
        'task_session_id': study_session.current_task_session_id
    }
    return HttpResponse(template.render(context, request))

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

    if User.objects.filter(first_name=first_name, last_name=last_name).exists():
        return json_response({
            'access_code': 'USER_EXISTS'
        })
    else:
        # make access code for user
        access_code = first_name.lower() + '-' + last_name.lower()
        User.objects.create(
            first_name = first_name,
            last_name = last_name,
            access_code = access_code
        )
        return json_response({
            'access_code': access_code
        })

def user_login(request):
    """

    Args:
        access_code
        check_existing_session

    Create a container for the new study session.

    """
    access_code = request.GET['access_code']
    check_existing_session = request.GET['check_existing_session']
    try:
        user = User.objects.get(access_code=access_code)

        # check if an incomplete study session for the user exists
        if check_existing_session == "true":
            no_existing_session = False
            healthy_sessions = []
            for session in StudySession.objects\
                    .filter(user=user).filter(Q(status='running') | Q(status='training'))\
                    .order_by('creation_time'):
                try:
                    task_session = TaskSession.objects.get(
                        session_id=session.current_task_session_id)
                    if task_session.status == 'running' or \
                                    task_session.status == 'paused':
                        healthy_sessions.append(session)
                    else:
                        session.close('closed_with_error')
                except ObjectDoesNotExist:
                    # task session is corrupted
                    session.close('closed_with_error')
            if healthy_sessions:
                # close previous running sessions if not properly closed
                existing_sessions = healthy_sessions
                for session in existing_sessions[:-1]:
                    session.close('closed_with_error')
                session = existing_sessions[-1]
                # recreate a new container in case the original session is off
                # due to container issue
                task_session.create_new_container()
                # remember the study session id and the task session id with
                # cookies
                resp = JsonResponse({
                    "status": "RUNNING_STUDY_SESSION_FOUND",
                    "task_session_id": session.current_task_session_id,
                })
                resp.set_cookie('session_id', session.session_id)
                resp.set_cookie('task_session_id', session.current_task_session_id)
            else:
                no_existing_session = True

        if check_existing_session == "false" or no_existing_session:
            # register a new study session for the user
            session_id = '-'.join([access_code, "study_session",
                str(StudySession.objects.filter(user=user).count() + 1)])

            session = StudySession.objects.create(
                user = user,
                session_id = session_id,
                creation_time = timezone.now(),
                
		        status = 'training'
            )

            # initialize the first task session
            init_task_session_id = session.update_current_task_session_id()
            session.save()

            try:
                create_task_session(session)
                # remember the study session id and the task session id with
                # cookies
                resp = json_response({"task_session_id": init_task_session_id},
                                     status="SESSION_CREATED")
                resp.set_cookie('session_id', session_id)
                resp.set_cookie('task_session_id', init_task_session_id)
            except ObjectDoesNotExist:
                session.close('closed_with_error')
                resp = json_response(status='TASK_SESSION_CREATION_FAILED')
    except ObjectDoesNotExist:
        resp = json_response(status='USER_DOES_NOT_EXIST')

    return resp

def retrieve_access_code(request):
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']
    try:
        access_code = User.objects.get(first_name=first_name,
                                       last_name=last_name).access_code
        return JsonResponse({
            "access_code": access_code
        })
    except ObjectDoesNotExist:
        return JsonResponse({
            "access_code": 'USER_DOES_NOT_EXIST'
        })

def instruction(request):
    template = loader.get_template('instruction.html')
    context = {}
    return HttpResponse(template.render(context, request))