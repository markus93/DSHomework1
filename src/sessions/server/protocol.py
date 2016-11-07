from __future__ import print_function

import os
from socket import SHUT_RDWR
import fileinput


from ..common import *

DIRECTORY_FILES = '_files'
DIRECTORY_USERS = '_users'

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

    owned_files = []
    available_files = []

    for fname in os.listdir(DIRECTORY_USERS):
        with open(DIRECTORY_USERS + os.sep + fname, 'r') as f:

            # Owner is at the first line
            file_owner, _ = next(f).strip().split('\t')

            if user == file_owner:
                owned_files.append(fname)

            for line in f:
                file_editor, _ = line.strip().split('\t')

                if user == file_editor:
                    available_files.append(fname)
                    break

    return {'owned_files': owned_files, 'available_files': available_files}


def list_users(fname):

    users = []

    with open(DIRECTORY_USERS + os.sep + fname, 'r') as f:

        for line in f:
            file_editor, _ = line.strip().split('\t')
            users.append(file_editor)

    return users


def get_file(fname):

    with open(DIRECTORY_FILES + os.sep + fname, 'r') as f:
        return f.read()


def make_file(user, fname):

    with open(DIRECTORY_USERS + os.sep + fname, 'w') as f:
        print('{0}\t-1'.format(user) , file=f)

    with open(DIRECTORY_FILES + os.sep + fname, 'w') as f:
        print('', file=f)


def acquire_lock(user, fname, line_no):

    with open(DIRECTORY_USERS + os.sep + fname, 'w') as f:
        for line in f:
            file_editor, locked_line = line.strip().split('\t')

            if locked_line == line_no:

                return False

    for line in fileinput.input(DIRECTORY_USERS + os.sep + fname, inplace=True):
        file_editor, locked_line = line.strip().split('\t')

        if file_editor == user:
            print('{0}\t{1}'.format(user, line_no))
            break


def edit_line(user, fname, line_no, line_content, is_new_line=False):

    for i, line in enumerate(fileinput.input(DIRECTORY_USERS + os.sep + fname, inplace=True)):
        pass