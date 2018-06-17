#!/usr/bin/python3           # This is client.py file
import socket
import pickle as p
import random
import time                                        
from threading import Thread


def ListenForPackets(server):
    while True:
        message = p.loads(server.recv(1024))
        #if type(message) is list:
         #   for element in list:
          #      print(element)

        #else:
        print(message)


def __main__():
    username = "<" + input("Enter username: ") + ">"

    # create a socket object
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    # get local machine name
    host = socket.gethostname()                           
    port = 9999

    # connection to hostname on the port.
    serverSocket.connect((host, port))
    listenerThread = Thread(target=ListenForPackets, args=(serverSocket,))
    listenerThread.start()

    while True:        
        resp = username + ": " + str(random.randint(0,100))
        #resp = input(username + ": ")
        serverSocket.send(p.dumps(resp))
        time.sleep(2)
        
    serverSocket.close()


if __name__ == "__main__":
   __main__()
