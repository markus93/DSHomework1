# Imports----------------------------------------------------------------------
from socket import error as soc_err
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, timeout
from sessions.common import *
from threading import Thread


def __connect(srv):
    """
    Create socket, connect to server
    @param srv: server's address
    @type srv: (str, int)
    @return:
    @rtype: socket._socketobject
    """

    # Declaring TCP socket
    sock = socket(AF_INET, SOCK_STREAM)
    LOG.debug('Client socket created, descriptor %d' % sock.fileno())

    # Try connect to server
    try:
        sock.connect(srv)
    except soc_err as e:
        # In case we failed to connect to server, we should report error code
        LOG.error('Can\'t connect to %s:%d, error: %s' % (srv + (e,)))
        return RSP_CANT_CONNECT
    LOG.info('Client connected to %s:%d' % srv)
    LOG.debug('Local TCP socket is bound on %s:%d' % sock.getsockname())
    return sock


def disconnect(sock):
    """
    Disconnect from the server, close the TCP socket
    @param sock: TCP socket to close
    @type sock: socket._socketobject
    @return:
    @rtype:
    """

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
    """
    Send request to server, receive response
    @param srv: server socket address
    @type srv: (str, int)
    @param r_type: request type
    @type r_type: str
    @param args: request parameters/data
    @type args: dict[str, str|int|bool|list[str]]
    @param sock:
    @type sock: socket._socketobject
    @return:
    @rtype: dict[str, str|int|bool|list[str]]
    """

    try:
        n = tcp_send(sock, type=r_type, **args)
    except soc_err as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted sending the data to %s:%d, ' \
                  'error: %s' % (sock + (e,)))
        # ... and close socket
        disconnect(sock)
        return RSP_ERRTRANSM, [str(e)]

    LOG.info('Sent [%s] request, total bytes sent [%d]' \
             '' % (CTR_MSGS[r_type], n))

    # Request sent, start receiving response
    try:
        rsp = tcp_receive(sock)
    except soc_err as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted receiving the data from %s:%d, ' \
                  'error: %s' % (srv + (e,)))
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
    """
    Handles Server connection, calls method request and  handles error messages
    @param srv: server socket address
    @type srv: (str, int)
    @param args: dictionary, request parameters/data
    @type args: dict[str, str|int|bool|list[str]]
    @param r_type: request type
    @type r_type: str
    @param end_connection: boolean, whether connection left open or not
    @type end_connection: bool
    @return: tuple ( string:err_code, dictionary:response arguments )
    @rtype: (str, dict[str, str|int|bool|list[str]])
    """

    # Connecting to server
    sock = __connect(srv)

    # TODO check whether error

    # Reading given file
    try:

        # Check whether server can receive given file
        response = __request(srv, r_type, args, sock)

        err = response['status']

        if err != RSP_OK:
            LOG.error(err)
            if 'error_message' in response:
                err = response['error_message']
            else:
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
        # If not disconnected return sock also
        return err, response, sock


def get_files_req(srv, user):
    """
    Requests files list from server, divided into owned and available files
    @param srv: server socket address
    @type srv: (str, int)
    @param user: username
    @type user: str
    @return: tuple ( string:err_code, list:owned files, list: available files)
    @rtype: (str, list[str], list[str])
    """

    args = {'user': user}
    err, response = __handle_request(srv, args, REQ_LIST_FILES)

    owned_files = response['owned_files']
    available_files = response['available_files']

    return err, owned_files, available_files


def get_editors_req(srv, user, fname):
    """
    Requests editors (users who have access to file)
    @param srv: server socket address
    @type srv: (str, int)
    @param user: username
    @type user: str
    @param fname: file name
    @type fname: str
    @return: tuple ( string:err_code, list:editors)
    @rtype: (str, list[str])
    """

    args = {'user': user, 'fname': fname}
    err, response = __handle_request(srv, args, REQ_GET_USERS)

    if err == "":
        users = response['users']
    else:
        users = None

    return err, users


def create_file_req(srv, user, fname):
    """
    Requests creating new file
    @param srv: server socket address
    @type srv: (str, int)
    @param user: username
    @type user: str
    @param fname: file name
    @type fname: str
    @return: err_code
    @rtype: str
    """

    args = {'user': user, 'fname': fname}
    err, _ = __handle_request(srv, args, REQ_MAKE_FILE)

    return err


def open_file_req(srv, user, fname):
    """
    Requests opening given file (user must have access to file)
    @param srv: server socket address
    @type srv: (str, int)
    @param user: username
    @type user: str
    @param fname: file name
    @type fname: str
    @return: tuple (string:err_code, string: file content, socket: sock)
    @rtype: (str, str, socket._socketobject)
    """

    args = {'user': user, 'fname': fname}
    err, response, sock = __handle_request(srv, args, REQ_GET_FILE, end_connection=False)

    if err == "":
        file_cont = response['file']
    else:
        file_cont = None

    return err, file_cont, sock


def add_editor_req(srv, user, fname, edname):
    """
    Requests adding new editor to file (new user who can edit file)
    @param srv: server socket address
    @type srv: (str, int)
    @param user: file owner
    @type user: str
    @param fname: file name
    @type fname: str
    @param edname: editors name
    @type edname: str
    @return: err_code
    @rtype: str
    """

    args = {'user': user, 'fname': fname, 'editor': edname}
    err, _ = __handle_request(srv, args, REQ_ADD_EDITOR)

    return err


def remove_editor_req(srv, user, edname, fname):
    """
    Requests removing editor from file (user who can edit file)
    @param srv: server socket address
    @type srv: (str, int)
    @param user: file owner
    @type user: str
    @param fname: file name
    @type fname: str
    @param edname: editors name
    @type edname: str
    @return: err_code
    @rtype: str
    """

    args = {'user': user, 'fname': fname, 'editor': edname}
    err, _ = __handle_request(srv, args, REQ_REMOVE_EDITOR)

    return err


def send_new_edit_req(srv, user, fname, line_no, line_content, is_new_line):
    """
    Requests writing edited line to file
    @param srv: server socket address
    @type srv: (str, int)
    @param user: username
    @type user: str
    @param fname: file name
    @type fname: str
    @param line_no: line number
    @type line_no: int
    @param line_content: edited line
    @type line_content: str
    @param is_new_line: Is the line added?
    @type is_new_line: bool
    @return: err_code
    @rtype: str
    """

    args = {'user': user, 'fname': fname, 'line_no': line_no, 'line_content': line_content, 'is_new_line': is_new_line}

    err, _ = __handle_request(srv, args, REQ_EDIT_FILE)

    return err


def lock_line_req(srv, user, fname, line_no):
    """
    Requests locking a line to given user
    @param srv: server socket address
    @type srv: (str, int)
    @param user: username
    @type user: str
    @param fname: filename
    @type fname: str
    @param line_no: line number
    @type line_no: int
    @return: tuple (string:err_code, boolean:lock)
    @rtype: (str, bool)
    """

    args = {'user': user, 'fname': fname, 'line_no': line_no}
    err, response = __handle_request(srv, args, REQ_GET_LOCK)

    if err == "":
        lock = response['lock']
    else:
        lock = None

    return err, lock


class listen_for_edits(Thread):

    def __init__(self, srv, sock, q):
        """
       Listens for new edits to file and puts them to Queue (for GUI to receive)
       @param srv: server socket address
       @type srv: (str, int)
       @param sock: server socket
       @type sock: socket._socketobject
       @param q: queue
       @type q: Queue.Queue
       """

        super(listen_for_edits, self).__init__()

        self.srv = srv
        self.sock = sock
        self.q = q

        self._is_running = True


    def run(self):

        LOG.debug("Started listening for edits")

        # Loop until disconnected from server
        while self._is_running:

            try:
                # Waiting for response from server (line number and line content)
                rsp = tcp_receive(self.sock, 1)

            except timeout:
                continue

            except soc_err as e:
                # In case we failed in the middle of transfer we should report error
                LOG.error('Interrupted receiving the data from %s:%d, '
                          'error: %s' % (self.srv + (e,)))
                # ... and close socket
                disconnect(self.sock)
                break

            err = rsp['status']
            if err == RSP_OK:
                # Add tuple (line number, line content) to the queue
                line_no = rsp['line_no']
                line_content = rsp['line_content']
                self.q.put((line_no, line_content))
                LOG.debug(str(line_no) + " " + line_content)

            else:
                if err in ERR_MSGS.keys():
                    LOG.error('Server response code [%s]: %s' % (err, ERR_MSGS[err]))
                else:
                    LOG.error('Malformed server response [%s]' % err)