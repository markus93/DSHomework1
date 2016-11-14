# Parses arguments (IP, port and other stuff that is not done by GUI)
# And runs gui main method


# Imports----------------------------------------------------------------------
from argparse import ArgumentParser  # Parsing command line arguments
from os.path import abspath, sep
from sys import path, argv

from sessions.client.main import __info, ___VER
from sessions.client.main import initialize
from gui import main
from sessions.common import DEFAULT_SERVER_INET_ADDR,\
    DEFAULT_SERVER_PORT

# Main method -----------------------------------------------------------------
if __name__ == '__main__':
    # Find the script absolute path, cut the working directory
    a_path = sep.join(abspath(argv[0]).split(sep)[:-1])
    # Append script working directory into PYTHONPATH
    path.append(a_path)

    # Parsing arguments
    parser = ArgumentParser(description=__info(),
                            version = ___VER)
    parser.add_argument('-H', '--host',\
                        help='Server INET address '\
                        'defaults to %s' % DEFAULT_SERVER_INET_ADDR, \
                        default=DEFAULT_SERVER_INET_ADDR)
    parser.add_argument('-p', '--port', type=int,\
                        help='Server UDP port, '\
                        'defaults to %d' % DEFAULT_SERVER_PORT, \
                        default=DEFAULT_SERVER_PORT)
    args = parser.parse_args()

    #Init client variables
    initialize(args)

    # Run Colted GUI
    main()
