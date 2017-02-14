"""
Merge two databases.
"""

import sqlite3

if __name__ == '__main__':
    input_db_path = 'db-lucy-dylan-yue.sqlite3'
    target_db_path = 'db.sqlite3'

    input_db = sqlite3.connect(input_db_path)
    target_db = sqlite3.connect(target_db_path)

    input_cur = input_db.cursor()
    target_cur = target_db.cursor()

    tables = [
        'website_actionhistory',
        'website_container',
        'website_studysession',
        'website_tasksession',
        'website_user'
    ]

    for task_session, action, stdout, action_time in input_cur.execute(
            'SELECT task_session, action, stdout, action_time FROM ' +
            'website_actionhistory'):
        print(task_session, action, stdout, action_time)