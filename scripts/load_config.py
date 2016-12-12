from website.models import *
from website.filesystem import dict_2_JSON

import json
import datetime

def run():
    file = open('config.json', 'r')
    content = str(file.read())
    config = json.loads(content)
    task_duration = config['task_duration']
    for task in config['tasks']:
        type = task['type']
        answer = None
        if type == 'stdout':
            answer = task['answer']
        elif type == 'filesystem':
            answer = dict_2_JSON(task['answer'])
        else:
            raise Exception('unrecognized task type: {}'.format(type))
        Task.objects.create(
            type=task['type'],
            description=task['description'],
            initial_filesystem=dict_2_JSON(task['initial_filesystem']),
            answer=answer,
            duration=datetime.timedelta(seconds=task_duration),
        )
    for access_code in config['access_codes']:
        create_user(access_code)
