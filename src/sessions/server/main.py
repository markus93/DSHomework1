from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os

from .protocol import *

for dir in (DIRECTORY_FILES, DIRECTORY_USERS):
    if not os.path.exists(dir):
        os.makedirs(dir)

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(('', DEFAULT_SERVER_PORT))
server_socket.listen(5) # Might change

while True:

    client_socket, address = server_socket.accept()

    Thread(target=client_handler(client_socket, address)).start()
