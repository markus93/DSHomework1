import json
import os

from ..common import *

DIRECTORY_FILES = '_files'
DIRECTORY_USERS = '_users'

def client_handler(client_socket, address):

    def run():

        request = tcp_recive(client_socket)

        if request['type'] == REQ_LIST_FILES:
            tcp_send(client_socket,
                     status=RSP_OK,
                     **list_files(request['user']))

        else:
            pass

    return run


def tcp_send(sock, **data):
    sock.sendall(json.dumps(data))


def tcp_recive(sock):

    message_size = int(sock.recv(__RSP_MESSAGE_SIZE))

    message = sock.recv(message_size)
    data = json.loads(message)

    return data


def list_files(user):

    owned_files = []
    available_files = []

    for filename in os.listdir(DIRECTORY_USERS):
        with open(DIRECTORY_USERS + os.sep + filename, 'r') as f:

            # Owner is at the first line
            file_owner = next(f).strip()

            if user == file_owner:
                owned_files.append(filename)

            for line in f:
                file_editor = line.strip()

                if user == file_editor:
                    available_files.append(filename)
                    break

    return {'owned_files': owned_files, 'available_files': available_files}