'''
Common variables, methods and structures of the Text Editor modules

'''
# Imports----------------------------------------------------------------------

import struct
# TCP related constants -------------------------------------------------------
#
DEFAULT_SERVER_PORT = 7777
DEFAULT_SERVER_INET_ADDR = '127.0.0.1'


# Requests --------------------------------------------------------------------
__REQ_LIST_FILES = '1'
__CTR_MSGS = { __REQ_LIST_FILES:'List currently uploaded files'
              }
# Responses--------------------------------------------------------------------
__RSP_OK = '0'
__RSP_BADFORMAT = '1'
__RSP_MSGNOTFOUND = '2'
__RSP_UNKNCONTROL = '3'
__RSP_ERRTRANSM = '4'
__RSP_CANT_CONNECT = '5'
__ERR_MSGS = { __RSP_OK:'No Error',
               __RSP_BADFORMAT:'Malformed message',
               __RSP_MSGNOTFOUND:'Message not found by iD',
               __RSP_UNKNCONTROL:'Unknown control code',
               __RSP_ERRTRANSM:'Transmission Error',
               __RSP_CANT_CONNECT:'Can\'t connect to server'
               }
# Field separator for sending multiple values ---------------------------------
__MSG_FIELD_SEP = ':'

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
