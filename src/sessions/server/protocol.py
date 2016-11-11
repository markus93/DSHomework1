from __future__ import print_function

import pickle
import socket
import os
from Queue import Queue, Empty
from threading import Thread

from sessions.common import *

DIRECTORY_FILES = '_files'
DIRECTORY_OBJECTS = '_objects'

FILES = dict()
"""@type: dict[str, FileHandler]"""
USERS = dict()
"""@type: dict[str, User]"""


class ServerException(Exception):
    pass


def client_handler(client_socket):
    """Handle any request made by the client
    @param client_socket:
    @type client_socket: socket._socketobject
    @return:
    @rtype:
    """

    def run():

        request = tcp_receive(client_socket)

        try:
            if request['type'] == REQ_LIST_FILES:

                if not check_request_format(request, 'user'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:
                    tcp_send(client_socket,
                             status=RSP_OK,
                             **list_files(**request))

            elif request['type'] == REQ_GET_USERS:

                if not check_request_format(request, 'user', 'fname'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:
                    tcp_send(client_socket,
                             status=RSP_OK,
                             users=list_users(**request))

            elif request['type'] == REQ_GET_FILE:

                if not check_request_format(request, 'user', 'fname'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:
                    tcp_send(client_socket,
                             status=RSP_OK,
                             file=get_file(**request))

                    USERS[request['user']] = User(client_socket, request['user'], request['fname'])
                    USERS[request['user']].start()

            elif request['type'] == REQ_MAKE_FILE:

                if not check_request_format(request, 'user', 'fname'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:

                    make_file(**request)

                    tcp_send(client_socket,
                             status=RSP_OK)

            elif request['type'] == REQ_GET_LOCK:

                if not check_request_format(request, 'user', 'fname', 'line_no'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:

                    tcp_send(client_socket,
                             status=RSP_OK,
                             lock=acquire_lock(**request))

            elif request['type'] == REQ_EDIT_FILE:

                if not check_request_format(request, 'user', 'fname', 'line_no', 'line_content'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:

                    edit_line(**request)

                    tcp_send(client_socket,
                             status=RSP_OK)

            elif request['type'] == REQ_ADD_EDITOR:

                if not check_request_format(request, 'user', 'fname', 'editor'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:

                    add_editor(**request)

                    tcp_send(client_socket,
                             status=RSP_OK)

            elif request['type'] == REQ_REMOVE_EDITOR:

                if not check_request_format(request, 'user', 'fname', 'editor'):
                    tcp_send(client_socket,
                             status=RSP_BADFORMAT)

                else:

                    remove_editor(**request)

                    tcp_send(client_socket,
                             status=RSP_OK)

            else:
                tcp_send(client_socket, status=RSP_UNKNCONTROL)

        except ServerException as e:
            LOG.warning('Exception happened during handling the request: {0}'.format(e.message))
            tcp_send(client_socket, status=RSP_BADFORMAT, error_message=e.message)

        if request['type'] != REQ_GET_FILE:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()

    return run


def check_request_format(request, *fields):
    """Check if all the required fields are present in the request.
    @param request:
    @type request: dict[str, str|int|bool|list[str]]
    @param fields:
    @type fields: list[str]
    @return:
    @rtype: bool
    """
    return all(field in request for field in fields)


def list_files(user, **kwargs):
    """List files, that are available to user.
    @param user:
    @type user: str
    @return: Dictionary, with fields owned_files and available_files
    @rtype: dict[str, list[str]]
    """

    LOG.info('Listing files, that are available to {0}'.format(user))

    owned_files = []
    available_files = []

    for fname, file_handler in FILES.items():
        if user == file_handler.owner:
            owned_files.append(file_handler.fname)
        elif user in file_handler.users:
            available_files.append(file_handler.fname)

    return {'owned_files': owned_files, 'available_files': available_files}


def list_users(user, fname, **kwargs):
    """Users, who can edit the file.
    @param user: Request maker
    @type user: str
    @param fname: filename
    @type fname: str
    @return: List of usernames
    @rtype: list[str]
    """

    if FILES[fname].owner != user:
        LOG.warning('{0} was trying to access editors of {1} without permissions'.format(user, fname))
        raise ServerException('Must be owner to see editors')

    LOG.info('Listing users for {0}'.format(fname))
    return FILES[fname].users


def get_file(user, fname, **kwargs):
    """Return the whole file content, this request is made once per user at the start of the session.
    An long lived TCP is also made turing this request. (see client_handler)
    @param user: Request makers name
    @type user: str
    @param fname: Filename, whose content is requested
    @type fname: str
    @return: Contents of the file
    @rtype: str
    """

    if FILES[fname].owner != user and user not in FILES[fname].users:
        LOG.warning('{0} was trying to access {1} without permissions'.format(user, fname))
        raise ServerException('Don\'t have rights to access {0}'.format(fname))

    with open(DIRECTORY_FILES + os.sep + fname, 'r') as f:
        LOG.info('{0}-s content was given to {1}'.format(fname, user))
        return f.read()


def make_file(user, fname, **kwargs):
    """Make new file, user is marked as owner.
    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @return:
    @rtype:
    """

    if fname in FILES:
        LOG.warning('{0} tried to make file with an existing name: {1}'.format(user, fname))
        raise ServerException('File {0} already exists'.format(fname))

    with open(DIRECTORY_FILES + os.sep + fname, 'w') as f:
        print('', file=f)

    FILES[fname] = FileHandler(fname, user)
    FILES[fname].start()

    LOG.info('{0} made a new file: {1}'.format(user, fname))


def acquire_lock(user, fname, line_no, **kwargs):
    """Acquire lock for a line in a file.
    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @param line_no:
    @type line_no: int
    @return: Was the lock successfully made?
    @rtype: bool
    """

    if FILES[fname].owner != user and user not in FILES[fname].users:
        LOG.warning('{0} was trying to access {1} without permissions'.format(user, fname))
        raise ServerException('Don\'t have rights to access {0}'.format(fname))

    if FILES[fname].locks.get(line_no, user) != user:
        LOG.info('{0} failed to acquire a lock in {1} for line {2}'.format(user, fname, line_no))
        return False

    FILES[fname].release_lock(user)

    FILES[fname].locks[line_no] = user
    LOG.info('{0} acquired a lock in {1} for line {2}'.format(user, fname, line_no))
    return True


def edit_line(user, fname, line_no, line_content, is_new_line=False, **kwargs):
    """Edit a line in a file, the edit request is added to a queue.
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
    @rtype:
    """

    if FILES[fname].owner != user and user not in FILES[fname].users:
        LOG.warning('{0} was trying to access {1} without permissions'.format(user, fname))
        raise ServerException('Don\'t have rights to access {0}'.format(fname))

    if FILES[fname].locks.get(line_no, None) != user:
        LOG.warning('{0} was trying to edit {1} without locking a line'.format(user, fname))
        raise ServerException('Don\'t have lock on line {0}'.format(line_no))

    if not line_content.endswith('\n'):
        line_content += '\n'

    FILES[fname].file_changes.put((line_no, line_content, is_new_line, user))
    LOG.info('File change request was made by {0} for {1}'.format(user, fname))

    return True


def add_editor(user, fname, editor, **kwargs):
    """Give editing rights to a user.
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
        LOG.warning('{0} was trying to access editors of {1} without permissions'.format(user, fname))
        raise ServerException('Must be owner to change editors')

    if editor not in FILES[fname].users:
        FILES[fname].users.append(editor)
        LOG.info('{0} made {1} an editor of {2}'.format(user, editor, fname))


def remove_editor(user, fname, editor, **kwargs):
    """Remove editing rights from a user.
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
        LOG.warning('{0} was trying to access editors of {1} without permissions'.format(user, fname))
        raise ServerException('Must be owner to change editors')

    if user in FILES[fname].users:
        FILES[fname].users.remove(editor)
        LOG.info('{0} removed {1} from editors of {2}'.format(user, editor, fname))


class User(Thread):
    def __init__(self, user_socket, name, fname):
        """Keeps the long-lived TCP connection between the user and server open. Notifies the user about all the changes
        made to the file.
        @param user_socket: Socket, where to send updates about the file
        @type user_socket: socket._socketobject
        @param name: name of the user
        @type name: str
        @param fname: name of the file
        @type fname: str
        """
        super(User, self).__init__()

        self.name = name
        self.fname = fname
        self.socket = user_socket
        self.notifications = Queue()

        self._is_running = True
        self.daemon = True

    def run(self):

        while self._is_running:

            try:
                line_no, line_content, is_new_line = self.notifications.get(timeout=1)

                try:
                    tcp_send(self.socket, status=RSP_OK, line_no=line_no, line_content=line_content,
                             is_new_line=is_new_line)
                except socket.error:
                    LOG.info('Connection ended with {0} from client side'.format(self.name))
                    self.remove()
                    break

                LOG.info('User {0} notified of the change at line {1}'.format(self.name, line_no))

            except Empty:
                # LOG.debug('Empty queue at user {0}'.format(self.name))
                pass
        else:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def remove(self):
        """
        Called after closing the long-lived TCP connection between user and server.
        Releases the locked line and deletes the user object.
        @return:
        @rtype:
        """

        FILES[self.fname].release_lock(self.name)

        # Delete the user
        del USERS[self.name]


class FileHandler(Thread):
    def __init__(self, fname, owner, users=None):
        """For each file on the server, a FileHandler Thread is made. It is responsible for makeing changes to files
        and notifying th user through User threads.
        It also keeps track of all the locked lines in the files.
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
        """@type: dict[int, str]"""

        self._is_running = True
        # self.daemon = True

    def run(self):

        while self._is_running:

            try:
                # TODO: Handle line insertions correctly
                line_no, line_content, is_new_line, editor = self.file_changes.get(timeout=1)
                LOG.info('Line {0} edited in {1} (is_new_line = {2})'.format(line_no, self.fname, is_new_line))

                with open(os.sep.join((DIRECTORY_FILES, self.fname)), 'r+') as f:
                    lines = f.readlines()

                    if is_new_line:
                        lines.insert(line_no, line_content)

                        # Update locks
                        for key in sorted(self.locks.keys(), reverse=True):
                            if key <= line_no:
                                self.locks[key + 1] = self.locks.pop(key)

                    else:
                        lines[line_no] = line_content

                    f.seek(0)
                    f.truncate()

                    f.writelines(lines)

                # Notify users
                for user_name in self.users:
                    if user_name != editor and user_name in USERS:
                        USERS[user_name].notifications.put((line_no, line_content, is_new_line))

            except Empty:
                # LOG.debug('Empty queue at file {0}'.format(self.fname))
                pass

        # Save the FileHandler
        self._is_running = True
        self.file_changes = None
        pickle.dump(self, open(os.sep.join((DIRECTORY_OBJECTS, self.fname)), 'wb'))

    def __reduce__(self):
        return FileHandler, (self.fname, self.owner, self.users)

    def release_lock(self, user):
        """Release the users lock in this file
        @param user: User, whose lock is being released
        @type user: str
        @return: Was the lock found
        @rtype: bool
        """

        # Release the lock
        for line_no, lock_owner in self.locks.items():
            if user == lock_owner:
                LOG.info("{0} released lock on line {1} in file {2}".format(lock_owner, line_no, self.fname))
                del self.locks[line_no]
                return True

        return False
