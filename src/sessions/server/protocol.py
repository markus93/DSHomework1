from __future__ import print_function

import os
from socket import SHUT_RDWR
import fileinput
from Queue import Queue
from threading import Thread

from ..common import *

DIRECTORY_FILES = '_files'
DIRECTORY_USERS = '_users'

FILES = dict()
USERS = dict()


# TODO Error on acquire_lock function
# TODO implement REQ_ADD_EDITOR, REQ_REMOVE_EDITOR, edit_line
def client_handler(client_socket, address):

    def run():

        request = tcp_receive(client_socket)

        if request['type'] == REQ_LIST_FILES:

            if 'user' not in request:
                tcp_send(client_socket,
                         status=RSP_BADFORMAT)

            else:
                tcp_send(client_socket,
                        status=RSP_OK,
                        **list_files(request['user']))

        elif request['type'] == REQ_GET_USERS:

            if 'user' not in request or 'fname' not in request:
                tcp_send(client_socket,
                         status=RSP_BADFORMAT)

            else:
                tcp_send(client_socket,
                        status=RSP_OK,
                        users=list_users(request['fname']))

        elif request['type'] == REQ_GET_FILE:

            if 'user' not in request or 'fname' not in request:
                tcp_send(client_socket,
                         status=RSP_BADFORMAT)

            else:
                tcp_send(client_socket,
                        status=RSP_OK,
                        file=get_file(request['fname']))

        elif request['type'] == REQ_MAKE_FILE:

            if 'user' not in request or 'fname' not in request:
                tcp_send(client_socket,
                         status=RSP_BADFORMAT)

            else:

                make_file(request['user'], request['fname'])

                tcp_send(client_socket,
                        status=RSP_OK)

        elif request['type'] == REQ_GET_LOCK:

            if 'user' not in request or 'fname' not in request or 'line_no' not in request:
                tcp_send(client_socket,
                         status=RSP_BADFORMAT)

            else:

                tcp_send(client_socket,
                         status=RSP_OK,
                         lock=acquire_lock(request['user'], request['fname'], request['line_no']))

        elif request['type'] == REQ_EDIT_FILE:

            if 'user' not in request or 'fname' not in request or 'line_no' not in request or 'line_content' not in request:
                tcp_send(client_socket,
                         status=RSP_BADFORMAT)

            else:

                edit_line(request['user'], request['fname'], request['line_no'], request['line_content'], request['is_new_line'])

                tcp_send(client_socket,
                         status=RSP_OK)

        else:
            tcp_send(client_socket, status=RSP_UNKNCONTROL)

        # Close the connection
        client_socket.shutdown(SHUT_RDWR)
        client_socket.close()

    return run


def list_files(user):
    """List files, that are available to user.
    @param user:
    @type user: str
    @return: Dictionary, with fields owned_files and available_files
    @rtype: dict
    """

    owned_files = []
    available_files = []

    for fname, file_handler in FILES.items():
        if user == file_handler.owner:
            owned_files.append(file_handler.fname)
        elif user in file_handler.users.keys():
            available_files.append(file_handler.fname)

    return {'owned_files': owned_files, 'available_files': available_files}


def list_users(fname):
    """Users, who can edit the file
    @param fname: filename
    @type fname: str
    @return: List of usernames
    @rtype: list
    """

    return list(FILES[fname].users.keys())


def get_file(fname):

    with open(DIRECTORY_FILES + os.sep + fname, 'r') as f:
        return f.read()


def make_file(user, fname):

    with open(DIRECTORY_FILES + os.sep + fname, 'w') as f:
        print('', file=f)

    FILES[fname] = FileHandler(fname, user)


def acquire_lock(user, fname, line_no):
    pass


def edit_line(user, fname, line_no, line_content, is_new_line=False):

    FILES[fname].file_changes.add((line_no, line_content, is_new_line, user))


class User(Thread):

    def __init__(self, user_socket, name):
        super(User, self).__init__()

        self.name = name
        self.socket = user_socket
        self.notifications = Queue()

    def run(self):

        try:

            while True:

                line_no, line_content, is_new_line = self.notifications.get()

                tcp_send(self.socket, line_no=line_no, line=line_content, is_new_line=is_new_line)

        except KeyboardInterrupt:
            # TODO: save the stuff
            pass


class FileHandler(Thread):

    def __init__(self, fname, owner, users=None):
        super(FileHandler, self).__init__()

        if users is None:
            users = []

        self.fname = fname
        self.owner = owner
        self.users = {user.name: user for user in users}
        self.file_changes = Queue()

    def run(self):

        try:

            while True:

                # TODO: Handle line insertions correctly
                line_no, line_content, is_new_line, editor = self.file_changes.get()

                with open(os.sep.join(DIRECTORY_FILES, self.fname), 'r+') as f:
                    lines = f.readlines()

                    if is_new_line:
                        lines.insert(line_no, line_content)
                    else:
                        lines[line_no] = line_content

                    f.seek(0)
                    f.truncate()

                    f.writelines(lines)

                # Notify users
                for user_name, user in self.users.items():
                    if user_name != editor:
                        user.notifications.add((line_no, line_content, is_new_line))

        except KeyboardInterrupt:
            # TODO: save the stuff
            pass
