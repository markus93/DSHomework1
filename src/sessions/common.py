"""
Common variables, methods and structures of the Text Editor modules

"""
# Imports----------------------------------------------------------------------

import json
import logging

# Logging----------------------------------------------------------------------

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.NOTSET, format=FORMAT)  # Log only errors
LOG = logging.getLogger()

# TCP related constants -------------------------------------------------------
#
DEFAULT_SERVER_PORT = 7777
DEFAULT_SERVER_INET_ADDR = '127.0.0.1'
RSP_MESSAGE_SIZE = 8

# Requests --------------------------------------------------------------------
REQ_LIST_FILES = '1'
REQ_GET_USERS = '2'
REQ_GET_FILE = '3'
REQ_MAKE_FILE = '4'
REQ_GET_LOCK = '5'
REQ_EDIT_FILE = '6'
REQ_ADD_EDITOR = '7'
REQ_REMOVE_EDITOR = '8'
REQ_DELETE_LINE = '9'

CTR_MSGS = {REQ_LIST_FILES: 'List currently uploaded files',
            REQ_GET_USERS: 'List user for specified file)',
            REQ_GET_FILE: 'Return whole file contents',
            REQ_MAKE_FILE: 'Make a new file, add user as owner',
            REQ_GET_LOCK: 'Lock the specified line to your user',
            REQ_EDIT_FILE: 'Edit a line inside a file',
            REQ_ADD_EDITOR: 'Add an editor to a file owned by you',
            REQ_REMOVE_EDITOR: 'Remove an editor from a file owned by you',
            REQ_DELETE_LINE: 'Remove a line from file'
            }
# Responses--------------------------------------------------------------------
RSP_OK = '0'
RSP_BADFORMAT = '1'
RSP_MSGNOTFOUND = '2'
RSP_UNKNCONTROL = '3'
RSP_ERRTRANSM = '4'
RSP_CANT_CONNECT = '5'
ERR_MSGS = {RSP_OK: 'No Error',
            RSP_BADFORMAT: 'Malformed message',
            RSP_MSGNOTFOUND: 'Message not found by iD',
            RSP_UNKNCONTROL: 'Unknown control code',
            RSP_ERRTRANSM: 'Transmission Error',
            RSP_CANT_CONNECT: 'Can\'t connect to server'
            }
# Field separator for sending multiple values ---------------------------------
MSG_FIELD_SEP = ':'


# Common methods --------------------------------------------------------------


def tcp_send(sock, **data):
    """

    @param sock:
    @type sock: socket._socketobject
    @param data:
    @type data: dict[str, str|int|bool|list[str]]
    @return:
    @rtype: int
    """

    message = json.dumps(data)
    length_str = str(len(message))
    length_str = '0' * (RSP_MESSAGE_SIZE - len(length_str)) + length_str

    sock.sendall(length_str + message)

    return len(message)


def tcp_receive(sock, timeout=None):
    """

    @param sock:
    @type sock: socket._socketobject
    @return:
    @rtype: dict[str, str|int|bool|list[str]]
    """
    sock.settimeout(timeout)
    message_size = int(sock.recv(RSP_MESSAGE_SIZE))

    message = sock.recv(message_size)
    data = json.loads(message)

    return data
