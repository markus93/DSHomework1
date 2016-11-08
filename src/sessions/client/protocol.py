#Imports----------------------------------------------------------------------
import logging
from os import path, makedirs
from socket import error as soc_err
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from sessions.common import *

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.NOTSET, format=FORMAT)  # Log only errors
LOG = logging.getLogger()


def __connect(srv):
    '''Create socket, connect to server
    @param srv: tuple ( string:IP, int:port ), server's address
    @returns sock: Socket
    '''

    # Declaring TCP socket
    sock = socket(AF_INET, SOCK_STREAM)
    LOG.debug('Client socket created, descriptor %d' % sock.fileno())

    # Try connect to server
    try:
        sock.connect(srv)
    except soc_err as e:
        # In case we failed to connect to server, we should report error code
        LOG.error('Can\'t connect to %s:%d, error: %s' % (srv + (e,)))
        return RSP_CANT_CONNECT, [str(e)]
    LOG.info('Client connected to %s:%d' % srv)
    LOG.debug('Local TCP socket is bound on %s:%d' % sock.getsockname())
    return sock

def disconnect(sock):
    '''Disconnect from the server, close the TCP socket
    @param sock: TCP socket to close
    @param srv: tuple ( string:IP, int:port ), server's address
    '''

    # Check if the socket is closed disconnected already ( in case there can
    # be no I/O descriptor
    try:
        sock.fileno()
    except soc_err:
        LOG.debug('Socket closed already ...')
        return

    # Closing RX/TX pipes
    LOG.debug('Closing client socket ...')
    # Close socket, remove I/O descriptor

    sock.close()
    LOG.info('Disconnected from server')


def __request(srv, r_type, args, sock):
    '''Send request to server, receive response
    @param srv: tuple ( IP, port ), server socket address
    @param r_type: string, request type
    @param args: dictionary, request parameters/data
    @returns dictionary: response
    '''

    n = 0   # Number of bytes sent
    try:
        n = tcp_send(sock, type=r_type, **args)
    except soc_err as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted sending the data to %s:%d, '\
                    'error: %s' % (sock+(e,)))
        # ... and close socket
        disconnect(sock)
        return RSP_ERRTRANSM,[str(e)]

    LOG.info('Sent [%s] request, total bytes sent [%d]'\
             '' % (CTR_MSGS[r_type], n))

    # Request sent, start receiving response
    rsp = None
    try:
        rsp = tcp_receive(sock)
    except (soc_err) as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted receiving the data from %s:%d, '\
                  'error: %s' % (srv+(e,)))
        # ... and close socket
        disconnect(sock)
        return RSP_ERRTRANSM, [str(e)]

    LOG.debug('Received response [%d bytes] in total' % len(rsp))

    # Check error code
    err = rsp['status']
    if err != RSP_OK:
        if err in ERR_MSGS.keys():
            LOG.error('Server response code [%s]: %s' % (err, ERR_MSGS[err]))
        else:
            LOG.error('Malformed server response [%s]' % err)

    return rsp


def __handle_request(srv, args, r_type, end_connection=True):
    '''
    Handles Server connection, calls method request and  handles error messages
    @param srv: tuple ( IP, port ), server socket address
    @param args: dictionary, request parameters/data
    @param r_type: string, request type
    @param end_connection: boolean, whether connection left open or not
    @returns tuple ( string:err_code, dictionary:response arguments )
    '''

    # Connecting to server
    sock = __connect(srv)

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, r_type, args, sock)

        err = response['status']

        if (err != RSP_OK):
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    # Disconnects from server
    if end_connection:

        sock.shutdown(SHUT_RDWR)  # Shutdown connection

        # Disconnect from server
        disconnect(sock)

        return err, response
    else:
        #If not disconnected return sock also
        return err, response, sock


def get_files_req(srv, user):
    '''
    Requests files list from server, divided into owned and available files
    @param srv: tuple ( IP, port ), server socket address
    @param user: string, username
    @returns tuple ( string:err_code, list:owned files, list: available files)
    '''

    args = {'user': user}
    err, response = __handle_request(srv, args, REQ_LIST_FILES)

    owned_files = response['owned_files']
    available_files = response['available_files']

    return err, owned_files, available_files


def get_editors_req(srv, fname):
    '''
    Requests editors (users who have access to file)
    @param srv: tuple ( IP, port ), server socket address
    @param fname: string, file name
    @returns tuple ( string:err_code, list:editors)
    '''

    args = {'fname': fname}
    err, response = __handle_request(srv, args, REQ_GET_USERS)

    users = response['users']

    return err, users


def create_file_req(srv, user, fname):
    '''
    Requests creating new file
    @param srv: tuple ( IP, port ), server socket address
    @param user: string, username
    @param fname: string, file name
    @returns string:err_code
    '''

    args = {'user': user, 'fname': fname}
    err, _ = __handle_request(srv, args, REQ_MAKE_FILE)

    return err


def open_file_req(srv, user, fname):
    '''
    Requests opening given file (user must have access to file)
    @param srv: tuple ( IP, port ), server socket address
    @param user: string, username
    @param fname: string, file name
    @returns tuple (string:err_code, string: file content, socket: sock)
    '''

    args = {'user': user, 'fname': fname}
    err, response, sock = __handle_request(srv, args, REQ_GET_FILE, end_connection=False)
    file = response['file']

    return err, file, sock


def add_editor_req(srv, fname, edname):
    '''
    Requests adding new editor to file (new user who can edit file)
    @param srv: tuple ( IP, port ), server socket address
    @param edname: string, name of editor
    @param fname: string, file name
    @returns string:err_code
    '''

    args = {'user': edname, 'fname': fname}
    err, _ = __handle_request(srv, args, REQ_ADD_EDITOR)

    return err


def remove_editor_req(srv, edname, fname):
    '''
    Requests removing editor from file (user who can edit file)
    @param srv: tuple ( IP, port ), server socket address
    @param edname: string, name of editor
    @param fname: string, file name
    @returns string:err_code
    '''

    args = {'user': edname, 'fname': fname}
    err, _ = __handle_request(srv, args, REQ_REMOVE_EDITOR)

    return err


def send_new_edit_req(srv, user, fname, line_no, line_content, is_new_line):
    '''
    Requests writing edited line to file
    @param srv: tuple ( IP, port ), server socket address
    @param user: string, username
    @param fname: string, file name
    @param line_no: int, line number
    @param line_content: string, edited line
    @param is_new_line: string, file name
    @returns string:err_code
    '''

    args = {'user': user, 'fname': fname, 'line_no': line_no, 'line_content': line_content, 'is_new_line': is_new_line}

    err, _ = __handle_request(srv, args, REQ_EDIT_FILE)

    return err


def lock_line_req(srv, user, fname, line_no):
    '''
    Requests locking a line to given user
    @param srv: tuple ( IP, port ), server socket address
    @param user: string, username
    @param fname: string, file name
    @param line_no: int, line number
    @returns tuple (string:err_code, boolean:lock)
    '''

    args = {'user': user, 'fname': fname, 'line_no': line_no}
    err, response = __handle_request(srv, args, REQ_GET_LOCK)

    lock = response['lock']

    return err, lock


def listen_for_edits(srv, sock, q):
    '''
    Listens for new edits to file and puts them to Queue (for GUI to receive)
    @param srv: tuple ( IP, port ), server socket address
    @param sock: string, username
    @param q: string, file name
    '''

    #Loop until disconnected from server
    while True:

        rsp = None

        try:
            #Waiting for response from server (line number and line content)
            rsp = tcp_receive(sock)

        except soc_err as e:
            # In case we failed in the middle of transfer we should report error
            LOG.error('Interrupted receiving the data from %s:%d, ' \
                      'error: %s' % (srv + (e,)))
            # ... and close socket
            disconnect(sock)
            break

        err = rsp['status']
        if err == RSP_OK:
            # Add tuple (line number, line content) to the queue
            line_no = rsp['line_no']
            line_content = rsp['line_content']
            q.put((line_no, line_content))

        else:
            if err in ERR_MSGS.keys():
                LOG.error('Server response code [%s]: %s' % (err, ERR_MSGS[err]))
            else:
                LOG.error('Malformed server response [%s]' % err)
