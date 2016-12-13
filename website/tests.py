from django.test import TestCase
from .filesystem import *
from .models import Task

import pathlib
import datetime

class FilesystemTestCase(TestCase):
    def test_normalize_JSON(self):
        json1 = normalize_JSON('{"b":   null, "a"  :null }  ')
        json2 = normalize_JSON('''{
            "a":null,
            "b":null}''')
        expected = '{"a": null, "b": null}'
        self.assertEqual(json1, expected)
        self.assertEqual(json2, expected)

    def test_disk_2_dict(self):
        expected = {'test_directory_tree': {'dir1': {'dir2': {'file2.txt': None}}, 'file1.txt': None}}
        actual = disk_2_dict(pathlib.Path('website/test_directory_tree'))
        self.assertEqual(actual, expected)

class TaskTestCase(TestCase):
    def test_to_dict_stdout(self):
        task = Task(
            type='stdout',
            description='description here',
            initial_filesystem='{"a": null}',
            answer='answer here',
            duration=datetime.timedelta(seconds=1),
        )
        expected = {
            'type': 'stdout',
            'description': 'description here',
            'initial_filesystem': {
                'a': None
            },
            'answer': 'answer here',
            'duration': 1,
        }
        self.assertEqual(task.to_dict(), expected)

    def test_to_dict_filesystem(self):
        task = Task(
            type='filesystem',
            description='description here',
            initial_filesystem='{"a": null}',
            answer='{"b": null}',
            duration=datetime.timedelta(seconds=1),
        )
        expected = {
            'type': 'filesystem',
            'description': 'description here',
            'initial_filesystem': {
                'a': None
            },
            'answer': {
                'b': None,
            },
            'duration': 1,
        }
        self.assertEqual(task.to_dict(), expected)
