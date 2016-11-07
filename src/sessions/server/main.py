from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from .protocol import *


# Info-------------------------------------------------------------------------

___NAME = 'Colted'
___VER = '0.0.0.1'
___DESC = 'Collaborative Text Editor'
___BUILT = '2016-11-23'
___VENDOR = 'Copyright (c) 2016 DSLab'

def __info():
    return '%s version %s (%s) %s' % (___NAME, ___VER, ___BUILT, ___VENDOR)


def server_main(args):

    for directory in (DIRECTORY_FILES, DIRECTORY_USERS):
        if not os.path.exists(directory):
            os.makedirs(directory)

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', int(args.listenport))) #Port from arguments (default 7777)
    server_socket.listen(5) # Might change

    while True:

        client_socket, address = server_socket.accept()

        Thread(target=client_handler(client_socket, address)).start()
