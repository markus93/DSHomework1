#Imports----------------------------------------------------------------------
import logging
from os import path, makedirs
from socket import error as soc_err
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from sessions.common import *

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.NOTSET, format=FORMAT)  # Log only errors
LOG = logging.getLogger()


# Static functions ------------------------------------------------------------
def __connect(srv):
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

def __disconnect(sock):
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
    @returns tuple ( string:err_code, list:response arguments )
    '''

    # Envelope the request
    #req = MSG_FIELD_SEP.join([r_type]+map(str,args))
    #LOG.debug('Will send [%s] request, total size [%d]'\  '' % (CTR_MSGS[r_type], len(req)))

    # Try to Send request using TCP
    n = 0   # Number of bytes sent
    try:
        n = tcp_send(sock, type=r_type, **args)
    except soc_err as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted sending the data to %s:%d, '\
                    'error: %s' % (sock+(e,)))
        # ... and close socket
        __disconnect(sock)
        return RSP_ERRTRANSM,[str(e)]

    LOG.info('Sent [%s] request, total bytes sent [%d]'\
             '' % (CTR_MSGS[r_type], n))

    # We assume if we are here we succeeded with sending, and
    # we may start receiving
    rsp = None
    try:
        rsp = tcp_receive(sock)
    except (soc_err) as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted receiving the data from %s:%d, '\
                  'error: %s' % (srv+(e,)))
        # ... and close socket
        __disconnect(sock)
        return RSP_ERRTRANSM, [str(e)]

    # We assume if we are here we succeeded with receiving, and
    # we may close the socket and check the response
    LOG.debug('Received response [%d bytes] in total' % len(rsp))

    # Check error code
    err = rsp['status']
    if err != RSP_OK:
        if err in ERR_MSGS.keys():
            LOG.error('Server response code [%s]: %s' % (err, ERR_MSGS[err]))
        else:
            LOG.error('Malformed server response [%s]' % err)

    return rsp


def get_files_req(srv, user):

    # Connecting to server
    sock = __connect(srv)
    args = {'user': user}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_LIST_FILES, args, sock)

        err = response['status']
        owned_files = response['owned_files']
        available_files = response['available_files']

        if(err != RSP_OK):
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR) #Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err, owned_files, available_files

def get_editors_req(srv, fname):

    # Connecting to server
    sock = __connect(srv)
    args = {'fname': fname}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_GET_USERS, args, sock)

        err = response['status']
        users = response['users']

        if err != RSP_OK:
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR) #Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err, users

def create_file_req(srv, user, fname):

    # Connecting to server
    sock = __connect(srv)
    args = {'user': user, 'fname': fname}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_MAKE_FILE, args, sock)

        err = response['status']

        if err != RSP_OK:
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR) #Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err

def open_file_req(srv, user, fname):

    # Connecting to server
    sock = __connect(srv)
    args = {'user': user, 'fname': fname}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_GET_FILE, args, sock)

        err = response['status']
        file = response['file']

        if err != RSP_OK:
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR) #Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err, file

def add_editor_req(srv, edname, fname):
    # Connecting to server
    sock = __connect(srv)
    args = {'user': edname, 'fname': fname}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_ADD_EDITOR, args, sock)

        err = response['status']

        if err != RSP_OK:
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR)  # Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err

def remove_editor_req(srv, edname, fname):
    # Connecting to server
    sock = __connect(srv)
    args = {'user': edname, 'fname': fname}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_REMOVE_EDITOR, args, sock)

        err = response['status']

        if err != RSP_OK:
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR)  # Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err

def send_new_edit_req(srv, user, fname, line_no, line_content, is_new_line):
    # Connecting to server
    sock = __connect(srv)
    args = {'user': user, 'fname': fname, 'line_no': line_no, 'line_content': line_content, 'is_new_line': is_new_line}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_EDIT_FILE, args, sock)

        err = response['status']

        if err != RSP_OK:
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR)  # Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err

def lock_line_req(srv, user, fname, line_no):

    # Connecting to server
    sock = __connect(srv)
    args = {'user': user, 'fname': fname, 'line_no': line_no}

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, REQ_GET_LOCK, args, sock)

        err = response['status']
        lock = response['lock']

        if err != RSP_OK:
            err = ERR_MSGS[err]
        else:
            err = ""

    except IOError as e:
        LOG.error(str(e))

    sock.shutdown(SHUT_RDWR)  # Shutdown connection

    # Disconnect from server
    __disconnect(sock)

    return err, lock