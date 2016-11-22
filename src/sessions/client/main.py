# Main client methods

# Import------------------------------------------------------------------------

from __future__ import print_function
from sessions.client.protocol import *
from Queue import Queue
from threading import Thread

# Info-------------------------------------------------------------------------

___NAME = 'Colted'
___VER = '0.0.0.1'
___DESC = 'Collaborative Text Editor'
___BUILT = '2016-11-23'
___VENDOR = 'Copyright (c) 2016 DSLab'

# Variables

server = '127.0.0.1', 7777
"""@type: (str, int)"""
listen_socket = None
threadListen = None


def __info():
    return '%s version %s (%s) %s' % (___NAME, ___VER, ___BUILT, ___VENDOR)


def initialize(args):
    global server
    server = (args.host, int(args.port))


def get_files(user):
    """Get files owned by user and available for user.
    @param user: username
    @type user: str
    @return:tuple ( string:err_description, list:owned_files, list:available_files )
    @rtype: (str, list[str], list[str])
    """
    return get_files_req(server, user)


def get_editors(user, fname):
    """Get files owned by user and available for user.
    @param user: username
    @type user: str
    @param fname:
    @type fname: str
    @return: tuple ( string:err_description, list:users)
    @rtype: (str, list[str])
    """
    return get_editors_req(server, user, fname)


def create_file(user, fname):
    """
    Create new file
    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @return: err_description
    @rtype: str
    """
    return create_file_req(server, user, fname)


def open_file(user, fname):
    """
    Open file by name
    @param user: username (who wants to open given file)
    @type user: str
    @param fname: filename
    @type fname: str
    @return: tuple ( string:err_description, string:file_content)
    @rtype: (str, str, Queue.Queue)
    """
    global listen_socket, threadListen

    # Closes previous listening session
    if listen_socket is not None:
        stop_listening()

    err, file_cont, listen_socket = open_file_req(server, user, fname)
    q = Queue()

    if file_cont:
        threadListen = listen_for_edits(server, listen_socket, q)
        threadListen.start()

    return err, file_cont, q


def add_editor(user, fname, edname):
    """
    Add editor (user) for the file
    @param user: username (who wants to open given file)
    @type user: str
    @param fname: filename
    @type fname: str
    @param edname: editor name (who can edit file)
    @type edname: str
    @return: err_description
    @rtype: str
    """
    return add_editor_req(server, user, fname, edname)


def remove_editor(user, fname, edname):
    """
    Remove editor (user) for the file
    @param user: username (who wants to open given file)
    @type user: str
    @param fname: filename
    @type fname: str
    @param edname: editor name (who can edit file)
    @type edname: str
    @return: err_description
    @rtype: str
    """
    return remove_editor_req(server, user, edname, fname)


def send_new_edit(user, fname, line_no, line_content, is_new_line=False):
    """
    Send new edit to server (overwrites the line
    @param user: username
    @type user: str
    @param fname: filename
    @type fname: str
    @param line_no: line number
    @type line_no: int
    @param line_content: edited line
    @type line_content: str
    @param is_new_line: is creating new line requested
    @type is_new_line: bool
    @return: err_description
    @rtype: str
    """
    return send_new_edit_req(server, user, fname, line_no, line_content, is_new_line)


def lock_line(user, fname, line_no):
    """
    Try to lock line with given number
    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @param line_no:
    @type line_no: int
    @return: tuple ( string:err_description, boolean: is line locked)
    @rtype: (str, bool)
    """
    return lock_line_req(server, user, fname, line_no)

def delete_line(user, fname, line_no):
    """
    Delete line with given number
    @param user:
    @type user: str
    @param fname:
    @type fname: str
    @param line_no:
    @type line_no: int
    @return: err_description
    @rtype: str
    """

    return delete_line_req(server, user, fname, line_no)


def stop_listening():
    """
    Disconnects from server (listening socket)
    """
    global listen_socket, threadListen
    if threadListen != None:
        threadListen._is_running = False

    disconnect(listen_socket)
    listen_socket = None
