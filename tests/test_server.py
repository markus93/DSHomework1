# basic functionality tests for server side

import os
import sys
from unittest import TestCase
import time

sys.path.insert(0, os.path.abspath('../src/'))

from sessions.server.main import *

# No need to log turing testing
logging.disable(logging.CRITICAL)


class ServerTests(TestCase):

    def setUp(self):
        FILES['testfile1'] = FileHandler('testfile1', 'testuser1', ['testuser2', 'testuser3'])
        FILES['testfile2'] = FileHandler('testfile2', 'testuser1', [])
        FILES['testfile3'] = FileHandler('testfile3', 'testuser2', ['testuser1'])

        if not os.path.exists(DIRECTORY_FILES):
            os.makedirs(DIRECTORY_FILES)

    def test_check_request_format(self):
        self.assertTrue(check_request_format({'type': '1', 'fname': 'testfile'}, 'fname'))
        self.assertTrue(check_request_format({'type': '1', 'fname': 'testfile', 'user': 'testuser'}, 'fname', 'user'))
        self.assertFalse(check_request_format({'type': '1', 'fname': 'testfile'}, 'fname', 'user'))

    def test_list_files(self):

        owned = list_files('testuser1')['owned_files']
        available = list_files('testuser1')['available_files']
        self.assertItemsEqual(owned, ['testfile1', 'testfile2'])
        self.assertItemsEqual(available, ['testfile3'])

        owned = list_files('testuser2')['owned_files']
        available = list_files('testuser2')['available_files']
        self.assertItemsEqual(owned, ['testfile3'])
        self.assertItemsEqual(available, ['testfile1'])

        owned = list_files('testuser3')['owned_files']
        available = list_files('testuser3')['available_files']
        self.assertItemsEqual(owned, [])
        self.assertItemsEqual(available, ['testfile1'])

        owned = list_files('testuser_not_avilable')['owned_files']
        available = list_files('testuser_not_avilable')['available_files']
        self.assertItemsEqual(owned, [])
        self.assertItemsEqual(available, [])

    def test_list_users(self):

        with self.assertRaises(ServerException):
            list_users('testuser2', 'testfile1')

        with self.assertRaises(ServerException):
            list_users('testuser2', 'testfile2')

        self.assertItemsEqual(['testuser2', 'testuser3'], list_users('testuser1', 'testfile1')['users'])

    def test_add_editor(self):

        with self.assertRaises(ServerException):
            add_editor('testuser2', 'testfile1', 'testuser4')

        with self.assertRaises(ServerException):
            add_editor('testuser2', 'testfile2', 'testuser4')

        add_editor('testuser1', 'testfile1', 'testuser4')
        self.assertItemsEqual(['testuser2', 'testuser3', 'testuser4'], list_users('testuser1', 'testfile1')['users'])

    def test_remove_editor(self):

        with self.assertRaises(ServerException):
            remove_editor('testuser2', 'testfile1', 'testuser3')

        with self.assertRaises(ServerException):
            remove_editor('testuser2', 'testfile2', 'testuser4')

        remove_editor('testuser1', 'testfile1', 'testuser3')
        self.assertItemsEqual(['testuser2'], list_users('testuser1', 'testfile1')['users'])

    def test_file_editing(self):

        with self.assertRaises(ServerException):
            get_file('testuser2', 'testfile2')

        self.assertEqual(make_file('testuser1', 'testfile4'), {})

        with self.assertRaises(ServerException):
            edit_line('testuser1', 'testfile4', 1, 'This line wont appear')

        self.assertTrue(acquire_lock('testuser1', 'testfile4', 1))
        edit_line('testuser1', 'testfile4', 1, 'This line will appear')
        time.sleep(1)  # This must be here
        self.assertEqual('This line will appear\n', get_file('testuser1', 'testfile4')['file'])

        self.assertEqual(delete_file('testuser1', 'testfile4'), {})
