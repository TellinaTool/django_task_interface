"""
Merge two databases.
"""

import os
import sqlite3

def get_column_names(table):
    return (list(map(lambda x: x[0], table.description)))

if __name__ == '__main__':
    input_db_path = os.path.join('..', '')
    target_db_path = os.path.join('..', '')

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

    """actionhistory_cur = input_db.execute('SELECT * FROM website_actionhistory')
    print(list(map(lambda x: x[0], actionhistory_cur.description)))
    for id, action, action_time, task_session_id, stdout in input_cur.execute(
            'SELECT * FROM website_actionhistory'):
        print(id)
        target_cur.execute('INSERT INTO website_actionhistory (id, action, action_time, task_session_id, stdout) VALUES (?, ?, ?, ?, ?)',
                           (10000+id, action, action_time, task_session_id, stdout))
    target_db.commit()
    """

    """table_name = 'website_container'
    container_cur = input_db.execute('SELECT * FROM {}'.format(table_name))
    column_names = get_column_names(container_cur)
    for id, container_id, filesystem_name, port in input_cur.execute(
        'SELECT * FROM {}'.format(table_name)):
        print(id)
        target_cur.execute('INSERT INTO {} ({}, {}, {}, {}) VALUES (?, ?, ?, ?)'.format(table_name, column_names[0], column_names[1], column_names[2], column_names[3]), (10000+id, container_id, filesystem_name, port))
    target_db.commit() 
    """

    """table_name = 'website_studysession'
    container_cur = input_db.execute('SELECT * FROM {}'.format(table_name))
    column_names = get_column_names(container_cur)
    print(column_names)
    for row in input_cur.execute('SELECT * FROM {}'.format(table_name)):
        print('INSERT INTO {} {} VALUES {}'.format(table_name, tuple(column_names+['ip_address']), tuple(['?']*(len(column_names)+1))))
        try:
            target_cur.execute('INSERT INTO {} {} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'.format(table_name, tuple(column_names+['ip_address'])), 
                (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], 10000+row[9], row[10], ''))
        except sqlite3.IntegrityError:
            print(row[0])
    target_db.commit()
    """

    """table_name = 'website_tasksession'
    container_cur = input_db.execute('SELECT * FROM {}'.format(table_name))
    column_names = get_column_names(container_cur)
    print(column_names)
    for row in input_cur.execute('SELECT * FROM {}'.format(table_name)):
        print('INSERT INTO {} {} VALUES {}'.format(table_name, tuple(column_names), tuple(['?']*(len(column_names)))))
        try:
            target_cur.execute('INSERT INTO {} {} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'.format(table_name, tuple(column_names)),
                (row[0], row[1], row[2], row[3], row[4], row[5], row[6], 10000+row[7], row[8], row[9]))
        except sqlite3.IntegrityError:
            print(row[0])
    target_db.commit()
    """

    """table_name = 'website_user'
    container_cur = input_db.execute('SELECT * FROM {}'.format(table_name))
    column_names = get_column_names(container_cur)
    print(column_names)
    for row in input_cur.execute('SELECT * FROM {}'.format(table_name)):
        print('INSERT INTO {} {} VALUES {}'.format(table_name, tuple(column_names), tuple(['?']*(len(column_names)))))
        try:
            target_cur.execute('INSERT INTO {} {} VALUES (?, ?, ?, ?, ?, ?, ?)'.format(table_name, tuple(column_names)),
                (10000+row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
        except sqlite3.IntegrityError:
            print(row[0])
    target_db.commit()
    """
   
