"""
This script uses config.json to setup initial data in the database.

Run it with `python3 manage.py runscript load_config`.
"""

from website.models import *

import json
import datetime
import django.contrib.auth.models as auth

def run():
    """
    This is the 'main method' that must be implemented in order for runscript
    to run this script.
    See http://django-extensions.readthedocs.io/en/latest/runscript.html#introduction
    """

    # initialize database based on the configuration file
    file = open('config.json', 'r')
    content = str(file.read())
    config = json.loads(content)
    task_duration = config['task_duration_in_seconds']

    # create super user
    auth.User.objects.create_superuser(username=config['superuser']['username'],
                                       password=config['superuser']['password'],
                                       email='')
    for user in config['users']:
        first_name = user['first_name']
        last_name = user['last_name']
        access_code = first_name.lower() + '-' + last_name.lower()
        User.objects.create(
            first_name = first_name,
            last_name = last_name,
            access_code = access_code
        )
    for task in config['tasks']:
        type = task['type']
        if type == 'stdout':
            goal = task['goal']
        elif type == 'filesystem':
            goal = json.dumps(task['goal'])
        else:
            raise Exception('unrecognized task type: {}'.format(type))
        Task.objects.create(
            task_id = task['task_id'],
	        type=task['type'],
            description=task['description'],
            initial_filesystem=json.dumps(task['initial_filesystem']),
            goal=goal,
            duration=datetime.timedelta(seconds=task_duration),
        )
