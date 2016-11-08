# Main client methods

# Import------------------------------------------------------------------------

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
listen_socket = None
threadListen = None

def __info():
    return '%s version %s (%s) %s' % (___NAME, ___VER, ___BUILT, ___VENDOR)


def initialize(args):
    global server
    server = (args.host, int(args.port))


# Temporary testing by client, later add to separate folder
def client_test():

    #Create file
    err = create_file('test', 'testfile')
    print "Error: " + str(err)

    #Get file list
    err, own, avb = get_files('test')
    print "Error: " + str(err) + ", owned files: " + str(own) + ", available files: " + str(avb)

    #Get file content
    err, file, queue = open_file('test', own[0])
    print "Error: " + str(err) + ", file content: " + str(file)

    #Lock certain line for editing
    err, lock = lock_line('test', 'testfile', 0)
    print "Error: " + str(err) + ", lock: " + str(lock)

    #Edit line
    err = send_new_edit('test', 'testfile', 0, 'Hello!')
    print "Error: " + str(err)

    err, file, _ = open_file('test', own[0])
    print str(err) + " file content: " + str(file)

    #stop_listening()


def get_files(user):
    '''Get files owned by user and available for user.
    @param user: string, username
    @returns tuple ( string:err_description, list:owned_files, list:available_files )
    '''
    global server
    return get_files_req(server, user)


def get_editors(fname):
    '''Get files owned by user and available for user.
    @param user: string, username
    @returns tuple ( string:err_description, list:users)
    '''
    global server
    return get_editors_req(server, fname)


def create_file(user,fname):
    '''Create new file
    @param user: string, username (owner)
    @param fname: string, new filename
    @returns string:err_description
    '''
    global server
    return create_file_req(server, user, fname)


def open_file(user, fname):
    '''Open file by name
    @param user: string, username (who wants to open given file)
    @param fname: string, filename
    @returns tuple ( string:err_description, string:file_content)
    '''
    global server, listen_socket, threadListen

    #Closes previous listening session TODO is old thread closed?
    if listen_socket != None:
        stop_listening()

    err, file_cont, listen_socket = open_file_req(server, user, fname)
    q = Queue();

    #threadListen = Thread(target=listen_for_edits(server, listen_socket, q))
    #threadListen.start() #TODO problem with listening

    return err, file_cont, q


#Not yet implemented by server side
def add_editor(fname, edname):
    '''Add editor (user) for the file
    @param fname: string, filename
    @param edname: string, editor name (who can edit file)
    @returns string:err_description
    '''
    global server
    return add_editor_req(server, fname, edname)


#Not yet implemented by server side
def remove_editor(fname, edname):
    '''Remove editor (user) for the file
    @param fname: string, filename
    @param edname: string, editor name (who can edit file)
    @returns string:err_description
    '''
    global server
    return add_editor_req(server, edname, fname)


#Not yet implemented by server side
def send_new_edit(user, fname, line_no, line_content, is_new_line=False):
    '''Send new edit to server (overwrites the line
    @param user: string, username
    @param fname: string, filename
    @param line_no: int, line number
    @param line_content: string, edited line
    @param is_new_line: boolean, is creating new line requested
    @returns string:err_description
    '''
    global server
    return send_new_edit_req(server, user, fname, line_no, line_content, is_new_line)


def lock_line(user, fname, line_no):
    '''
    @param user:
    @param fname:
    @param line_no:
    @returns tuple ( string:err_description, boolean: is line locked)
    '''
    global server
    return lock_line_req(server, user, fname, line_no)


def stop_listening():
    '''
    Disconnects from server (listening socket)
    '''
    global listen_socket
    disconnect(listen_socket)
    listen_socket = None
    #TODO clear queue?
