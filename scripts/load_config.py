"""
This script uses config.json to setup initial data in the database.

Run it with `python3 manage.py runscript load_config`.
"""

from website.models import *

import json
import datetime

def run():
    """
    This is the 'main method' that must be implemented in order for runscript
    to run this script.
    See http://django-extensions.readthedocs.io/en/latest/runscript.html#introduction
    """
    file = open('config.json', 'r')
    content = str(file.read())
    config = json.loads(content)
    task_duration = config['task_duration_in_seconds']
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
