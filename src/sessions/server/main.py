from __future__ import print_function

from sessions.server.protocol import *

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

    LOG.info('Starting up the server')
    LOG.info('Creating directories')
    for directory in (DIRECTORY_FILES, DIRECTORY_OBJECTS):
        if not os.path.exists(directory):
            os.makedirs(directory)

    LOG.info('Initializing file handlers')
    for fname in os.listdir(DIRECTORY_OBJECTS):
        FILES[fname] = pickle.load(open(DIRECTORY_OBJECTS + os.sep + fname, 'rb'))
        FILES[fname].start()

    LOG.info('Setting up the socket')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', int(args.listenport)))  # Port from arguments (default 7777)
    server_socket.listen(5)  # Might change
    LOG.info('Ready for connections')

    try:

        while True:

            client_socket, address = server_socket.accept()
            LOG.debug('Connection made with {0}'.format(address))

            client_thread = Thread(target=client_handler(client_socket))
            client_thread.daemon = True
            client_thread.start()

    except (KeyboardInterrupt, SystemExit):
        # On Windows we don't make it to here :(
        LOG.info('Shutting down...')

    except Exception as e:
        LOG.info('Error occured: shutting down...')
        raise e
    finally:

        server_socket.shutdown(socket.SHUT_RDWR)
        server_socket.close()

        LOG.info('Shuting down threads')
        for user in USERS.values():
            user._is_running = False

        for file_handler in FILES.values():
            file_handler._is_running = False

        for file_handler in FILES.values():
            file_handler.join()
