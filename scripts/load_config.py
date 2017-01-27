"""
This script uses config.json to setup initial data in the database.

Run it with `python3 manage.py runscript load_config`.
"""

from website.constants import *
from website.models import *
from website.filesystem import *

import json
import os
import datetime
import django.contrib.auth.models as auth
from django.core.exceptions import ObjectDoesNotExist

def run():
    """
    This is the 'main method' that must be implemented in order for runscript
    to run this script.
    See http://django-extensions.readthedocs.io/en/latest/runscript.html#introduction
    """

    json_dir = 'data/'

    # initialize database based on the configuration file
    file = open(os.path.join(json_dir, 'config.json'), 'r')
    content = str(file.read())
    config = json.loads(content)
    task_duration = config['task_duration_in_seconds']

    # register super user
    superuser_name = config['superuser']['username']
    superuser_passwd = config['superuser']['password']
    try:
        auth.User.objects.get_by_natural_key(username=superuser_name)
    except ObjectDoesNotExist:
        auth.User.objects.create_superuser(username=superuser_name,
                                           password=superuser_passwd, email='')
    # register users
    for user in config['users']:
        first_name = user['first_name']
        last_name = user['last_name']
        group = user['group']
        access_code = first_name.lower() + '-' + last_name.lower()
        if not User.objects.filter(access_code=access_code).exists():
            User.objects.create(
                first_name = first_name, last_name = last_name,
                access_code = access_code, group = group
            )

    # register tasks
    for file_name in os.listdir('data'):
        if file_name.startswith('task') and file_name.endswith('.json') \
                and not 'stdout' in file_name:
            print("load task json file {}...".format(file_name))
            file = open(os.path.join('data/', file_name), 'r')
            content = str(file.read())
            # skip empty task files
            if not content:
                continue
            task = json.loads(content)
            if not Task.objects.filter(task_id=task['task_id']).exists():
                file_attributes = json.dumps(task["file_attributes"])
                if task['type'] == "stdout":
                    with open(os.path.join('data/', 'task{}.stdout.json'
                            .format(task['task_id'])), 'r') as f:
                        stdout = f.read()
                else:
                    stdout = ''
                solution = task['solution'] if 'solution' in task else ''
                Task.objects.create(
                    task_id = task['task_id'],
                    type=task['type'],
                    description=task['description'],
                    file_attributes = file_attributes,
                    goal_filesystem = json.dumps(
                        filesystem_sort(task['goal_filesystem'])),
                    stdout=stdout,
                    duration=datetime.timedelta(seconds=task_duration),
                    solution = solution
                )