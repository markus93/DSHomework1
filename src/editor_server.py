# Imports----------------------------------------------------------------------
from argparse import ArgumentParser  # Parsing command line arguments
from os.path import abspath, sep
from sys import path, argv

from sessions.common import DEFAULT_SERVER_INET_ADDR,\
    DEFAULT_SERVER_PORT
from sessions.server.main import __info, ___VER, \
    server_main


# Main method -----------------------------------------------------------------
if __name__ == '__main__':
    # Find the script absolute path, cut the working directory
    a_path = sep.join(abspath(argv[0]).split(sep)[:-1])
    # Append script working directory into PYTHONPATH
    path.append(a_path)

    # Parsing arguments
    parser = ArgumentParser(description=__info(),
                            version = ___VER)
    parser.add_argument('-p','--listenport', \
                        help='Bind server socket to UDP port, '\
                        'defaults to %d' % DEFAULT_SERVER_PORT, \
                        default=DEFAULT_SERVER_PORT)

    args = parser.parse_args()

    # Run Colted server
    server_main(args)
