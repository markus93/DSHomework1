from __future__ import print_function

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

from .protocol import *

# Info-------------------------------------------------------------------------

___NAME = 'Colted'
___VER = '0.0.0.1'
___DESC = 'Collaborative Text Editor'
___BUILT = '2016-11-23'
___VENDOR = 'Copyright (c) 2016 DSLab'


def __info():
    return '%s version %s (%s) %s' % (___NAME, ___VER, ___BUILT, ___VENDOR)

# Main-------------------------------------------------------------------------


def server_main(args):
    """

    @param args:
    @type args:
    @return:
    @rtype:
    """

    for directory in (DIRECTORY_FILES, DIRECTORY_USERS):
        if not os.path.exists(directory):
            os.makedirs(directory)

    # TODO: populate FILES and USERS

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(('', int(args.listenport)))  # Port from arguments (default 7777)
    server_socket.listen(5)  # Might change

    try:
        while True:

            client_socket, address = server_socket.accept()

            client_thread = Thread(target=client_handler(client_socket))
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        LOG.info('Shutting down...')

    except Exception as e:
        LOG.info('Error occured: shutting down...')
        raise e
    finally:

        server_socket.shutdown(SHUT_RDWR)
        server_socket.close()

        LOG.info('Shuting down threads')
        # Shut down all threads
        for user in USERS.values():
            user._is_running = False

        for file_handler in FILES.values():
            file_handler._is_running = False
