'''
Common variables, methods and structures of the Text Editor modules

'''
# Imports----------------------------------------------------------------------

import struct
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

CTR_MSGS = {REQ_LIST_FILES: 'List currently uploaded files',
            REQ_GET_USERS: 'List user for specified file)',
            REQ_GET_FILE: 'Return whole file contents',
            REQ_MAKE_FILE: 'Make a new file, add user as owner',
            REQ_GET_LOCK: 'Lock the specified line to your user',
            REQ_EDIT_FILE: 'Edit a line inside a file',
            REQ_ADD_EDITOR: 'Add an editor to a file owned by you',
            REQ_REMOVE_EDITOR: 'Remove an editor from a file owned by you'
}
# Responses--------------------------------------------------------------------
RSP_OK = '0'
RSP_BADFORMAT = '1'
RSP_MSGNOTFOUND = '2'
RSP_UNKNCONTROL = '3'
RSP_ERRTRANSM = '4'
RSP_CANT_CONNECT = '5'
ERR_MSGS = { RSP_OK:'No Error',
               RSP_BADFORMAT:'Malformed message',
               RSP_MSGNOTFOUND:'Message not found by iD',
               RSP_UNKNCONTROL:'Unknown control code',
               RSP_ERRTRANSM:'Transmission Error',
               RSP_CANT_CONNECT:'Can\'t connect to server'
               }
# Field separator for sending multiple values ---------------------------------
MSG_FIELD_SEP = ':'

# Common methods --------------------------------------------------------------
def tcp_send(sock,data):
    '''Send data using TCP socket. Adds message length before message
    @param sock: TCP socket, used to send/receive
    @param data: The data to be sent
    @returns integer,  n bytes sent and error if any
    @throws socket.error in case of transmission error
    '''

    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(data)) + data

    sock.sendall(msg)
    return len(data)

def tcp_receive(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
