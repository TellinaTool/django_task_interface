from django.test import TestCase
from website.filesystem import *
import pathlib

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
