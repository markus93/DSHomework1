# basic functionality tests for client side

import os
import sys
from unittest import TestCase
import subprocess
import signal

sys.path.insert(0, os.path.abspath('../src/'))

from sessions.client.main import *

"""@type subproc: subprocess"""
subproc = None

# Helper class for creating args similar as given to main class
class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class ClientTests(TestCase):

    def setUp(self):
        #Setting up args
        args = Bunch(port=DEFAULT_SERVER_PORT, listenport=DEFAULT_SERVER_PORT, host=DEFAULT_SERVER_INET_ADDR)

        # Start server as subprocess
        global subproc
        subproc = subprocess.Popen(["python", "../src/editor_server.py"], shell=False)
        # client server variable set up
        initialize(args)


    # Test file creating, new file, file with same name
    def test_file_creating(self):
        status = create_file('user1', 'file1')
        self.assertEqual(status, "")  # Should only return empty err
        status = create_file('user1', 'file1')
        self.assertEqual(status, "File file1 already exists")  # Should return given error


    # Test file opening, whether such file exists, accessing unauthorized file
    def test_file_opening(self):
        create_file('user1', 'file1')
        # Normal file opening
        status, _, _ = open_file('user1', 'file1')
        self.assertEqual(status, "")  # Meaning no error
        # Unauthorized file opening
        status, _, _ = open_file('user2', 'file1')
        self.assertEqual(status, "Don't have rights to access file1")
        # Opening non-existing file
        #status, _, _ = open_file('user1', 'file2')  # TODO file existing is not controlled
        #self.assertEqual(status, "File file1 does not exist")

        # Stop edits listening thread properly
        stop_listening()


    # Test editor (user) adding - adding twice, add owner as editor
    def test_editor_adding(self):
        create_file('user1', 'file1')
        #Add editor (user) normally)
        status = add_editor('user1', 'file1', 'user2')
        self.assertEqual(status, "")
        #Add same editor twice
        status = add_editor('user1', 'file1', 'user2')  # Throws no error
        self.assertEqual(status, "")
        #Add owner as editor (user)
        status = add_editor('user1', 'file1', 'user1')  # TODO one can add himself as user
        #self.assertEqual(status, "Cannot add owner as user")
        #Add editor to available file (file that user does not own)
        status = add_editor('user2', 'file1', 'user3')
        self.assertEqual(status, "Must be owner to change editors")


    # Editor deleting - delete owner, delete editor twice
    def test_editor_removing(self):
        create_file('user1', 'file1')
        add_editor('user1', 'file1', 'user2')
        # Remove editor normally
        status = remove_editor('user1', 'file1', 'user2')
        self.assertEqual(status, "")
        # Remove editor second time
        status = remove_editor('user1', 'file1', 'user2')  # No error thrown
        self.assertEqual(status, "")
        # Try to remove owner non-existing user from editors
        status = remove_editor('user1', 'file1', 'nonexist')  # No error thrown
        self.assertEqual(status, "")
        # Try to remove user for available file (file that user does not own
        status = remove_editor('user2', 'file1', 'user1')
        self.assertEqual(status, "Must be owner to change editors")

    # Test file listing for different scenarios
    def test_file_listing(self):
        create_file('user1', 'file1')
        create_file('user1', 'file2')
        create_file('user2', 'file3')
        add_editor('user2', 'file3', 'user1')
        #List files for user1
        status, owned, available = get_files('user1')
        self.assertEqual(status, "")
        self.assertItemsEqual(owned, ['file1', 'file2'])
        self.assertItemsEqual(available, ['file3'])
        #List files for user2
        status, owned, available = get_files('user2')
        self.assertEqual(status, "")
        self.assertItemsEqual(owned, ['file3'])
        self.assertItemsEqual(available, [])
        #List files for new user
        status, owned, available = get_files('newuser')
        self.assertEqual(status, "")
        self.assertItemsEqual(owned, [])
        self.assertItemsEqual(available, [])

    # Test locking rows
    def test_locks(self):
        create_file('user1', 'file1')
        add_editor('user1', 'file1', 'user2')
        send_new_edit('user1', 'file1', 0, "abc", True)
        #Normal locking
        status, lock = lock_line('user1', 'file1', 0)
        self.assertEqual(status, "")
        self.assertTrue(lock)
        #Lock same row twice
        status, lock = lock_line('user1', 'file1', 0)
        self.assertEqual(status, "")
        self.assertTrue(lock)
        # Try to lock line, which is already locked
        status, lock = lock_line('user2', 'file1', 0)
        self.assertFalse(lock)
        #Try to lock line of non-existing file
        #status, lock = lock_line('user1', 'file2', 0)  # TODO file existing is not controlled
        #print status + " " + str(lock)
        #Try to lock line of non-existing line
        status, lock = lock_line('user1', 'file1', 5)  # TODO shouldn't be able to lock non-existing line?
        self.assertEqual(status, "")
        self.assertTrue(lock)
        #Try to lock line of not available file
        status, lock = lock_line('user3', 'file1', 0)
        self.assertEqual(status, "Don't have rights to access file1")
        #Check if previously locked line is released and new line locked
        status, lock = lock_line('user1', 'file1', 1)
        self.assertTrue(lock)
        status, lock = lock_line('user2', 'file1', 0)
        self.assertTrue(lock)

    # Test editor (user) listing
    def test_get_editors(self):
        create_file('user1', 'file1')
        add_editor('user1', 'file1', 'user2')
        add_editor('user1', 'file1', 'user3')
        #Get editors normally
        status, editors = get_editors('user1', 'file1')
        self.assertEqual(status, "")
        self.assertItemsEqual(editors, ['user2', 'user3'])
        #Get editors of not-existing file
        #status, _ = get_editors('user1', 'nonexist') #TODO file existing is not controlled
        #self.assertEqual(status, "Malformed message")
        #Get editor with not-allowed user
        status, _ = get_editors('user2', 'file1')
        self.assertEqual(status, "Must be owner to see editors")

    # Test sending line changes
    def test_edit_line(self):
        pass



    def tearDown(self):

        #Clear old files
        folder = '../tests/_files/'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        # shutdown server
        subproc.terminate()
        print "Tear down done."


# Adding line - on wrong line (that is not locked?), line that does not exist
#Multiple users with same name

