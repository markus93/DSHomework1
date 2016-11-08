from __future__ import print_function

import os
from socket import SHUT_RDWR
from Queue import Queue, Empty
from threading import Thread

from ..common import *

DIRECTORY_FILES = '_files'
DIRECTORY_USERS = '_users'

FILES = dict()
"""@type: dict[str, FileHandler]"""
USERS = dict()
"""@type: dict[str, User]"""


class ServerException(Exception):
    pass


def client_handler(client_socket):
    """

    @param client_socket:
    @type client_socket: socket.socket
    @return:
    @rtype:
    """

    def run():

        request = tcp_receive(client_socket)

        try:
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
                             users=list_users(request['user'], request['fname']))

            elif request['type'] == REQ_GET_FILE:

                if 'user' not in request or 'fname' not in request:
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:
                    tcp_send(client_socket,
                             status=RSP_OK,
                             file=get_file(request['user'], request['fname']))

                    USERS[request['user']] = User(client_socket, request['user'])
                    USERS[request['user']].start()
                    FILES[request['fname']].users.append(request['user'])

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

                    edit_line(request['user'], request['fname'], request['line_no'], request['line_content'],
                              request['is_new_line'])

                    tcp_send(client_socket,
                             status=RSP_OK)

            elif request['type'] == REQ_ADD_EDITOR:

                if 'user' not in request or 'fname' not in request or 'editor' not in request:
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:

                    add_editor(request['user'], request['fname'], request['editor'])

                    tcp_send(client_socket,
                             status=RSP_OK)

            elif request['type'] == REQ_REMOVE_EDITOR:

                if 'user' not in request or 'fname' not in request or 'editor' not in request:
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:

                    remove_editor(request['user'], request['fname'], request['editor'])

                    tcp_send(client_socket,
                             status=RSP_OK)

            else:
                tcp_send(client_socket, status=RSP_UNKNCONTROL)

        except ServerException as e:
            tcp_send(client_socket, status=RSP_BADFORMAT, error_message=e.args)

        if request['type'] != REQ_GET_FILE:
            client_socket.shutdown(SHUT_RDWR)
            client_socket.close()

    return run


def list_files(user):
    """List files, that are available to user.
    @param user:
    @type user: str
    @return: Dictionary, with fields owned_files and available_files
    @rtype: dict[str, list[str]]
    """

    owned_files = []
    available_files = []

    for fname, file_handler in FILES.items():
        if user == file_handler.owner:
            owned_files.append(file_handler.fname)
        elif user in file_handler.users:
            available_files.append(file_handler.fname)

    return {'owned_files': owned_files, 'available_files': available_files}


def list_users(user, fname):
    """Users, who can edit the file
    @param user: Request maker
    @type user: str
    @param fname: filename
    @type fname: str
    @return: List of usernames
    @rtype: list[str]
    """

    if FILES[fname].owner != user:
        raise ServerException('Must be owner to see editors')

    return FILES[fname].users


def get_file(user, fname):
    """
    @param user: Request makers name
    @type user: str
    @param fname: Filename, whose content is requested
    @type fname: str
    @return:
    @rtype: str
    """

    if FILES[fname].owner != user and user not in FILES[fname].users:
        raise ServerException('Don\'t have rights to access {0}'.format(fname))

    with open(DIRECTORY_FILES + os.sep + fname, 'r') as f:
        return f.read()


def make_file(user, fname):
    """

    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @return:
    @rtype:
    """

    if fname in FILES:
        raise ServerException('File {0} already exists'.format(fname))

    with open(DIRECTORY_FILES + os.sep + fname, 'w') as f:
        print('', file=f)

    FILES[fname] = FileHandler(fname, user)
    FILES[fname].start()


def acquire_lock(user, fname, line_no):
    """

    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @param line_no:
    @type line_no: int
    @return:
    @rtype: bool
    """

    if FILES[fname].locks.get(line_no, user) != user:
        return False

    FILES[fname].locks[line_no] = user
    return True


def edit_line(user, fname, line_no, line_content, is_new_line=False):
    """

    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @param line_no:
    @type line_no: int
    @param line_content:
    @type line_content: str
    @param is_new_line:
    @type is_new_line: bool
    @return:
    @rtype: bool
    """

    if FILES[fname].owner != user and user not in FILES[fname].users:
        raise ServerException('Don\'t have rights to access {0}'.format(fname))

    FILES[fname].file_changes.put((line_no, line_content, is_new_line, user))

    return True


def add_editor(user, fname, editor):
    """
    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @param editor:
    @type editor: str
    @return:
    @rtype:
    """

    if FILES[fname].owner != user:
        raise ServerException('Must be owner to change editors')

    FILES[fname].users.append(editor)


def remove_editor(user, fname, editor):
    """
    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @param editor:
    @type editor: str
    @return:
    @rtype:
    """

    if FILES[fname].owner != user:
        raise ServerException('Must be owner to change editors')

    FILES[fname].users.remove(editor)


class User(Thread):
    def __init__(self, user_socket, name):
        """
        @param user_socket:
        @type user_socket: socket.socket
        @param name:
        @type name: str
        """
        super(User, self).__init__()

        self.name = name
        self.socket = user_socket
        self.notifications = Queue()

        self._is_running = True
        self.daemon = True

    def run(self):

        while self._is_running:

            try:
                line_no, line_content, is_new_line = self.notifications.get(timeout=1)

                tcp_send(self.socket, line_no=line_no, line=line_content, is_new_line=is_new_line)

            except Empty:
                # LOG.debug('Empty que at user {0}'.format(self.name))
                pass

        self.socket.shutdown(SHUT_RDWR)
        self.socket.close()
        # TODO: save


class FileHandler(Thread):
    def __init__(self, fname, owner, users=None):
        """
        @param fname:
        @type fname: str
        @param owner:
        @type owner: str
        @param users:
        @type users: list[str]
        """
        super(FileHandler, self).__init__()

        if users is None:
            users = []

        self.fname = fname
        self.owner = owner
        self.users = users
        self.file_changes = Queue()
        self.locks = dict()

        self._is_running = True
        # self.daemon = True

    def run(self):

        while self._is_running:

            try:
                # TODO: Handle line insertions correctly
                line_no, line_content, is_new_line, editor = self.file_changes.get(timeout=1)

                with open(os.sep.join((DIRECTORY_FILES, self.fname)), 'r+') as f:
                    lines = f.readlines()

                    if is_new_line:
                        lines.insert(line_no, line_content)

                        # Update locks
                        for key in sorted(self.locks.keys(), reverse=True):
                            if key <= line_content:
                                self.locks[key + 1] = self.locks.pop(key)

                    else:
                        lines[line_no] = line_content

                    f.seek(0)
                    f.truncate()

                    f.writelines(lines)

                # Notify users
                for user_name in self.users:
                    if user_name != editor:
                        USERS[user_name].notifications.put((line_no, line_content, is_new_line))

            except Empty:
                # LOG.debug('Empty que at file {0}'.format(self.fname))
                pass

                # TODO: save the stuff
