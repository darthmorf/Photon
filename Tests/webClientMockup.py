#!/usr/bin/python3           # This is client.py file

import socket

# create a socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

# get local machine name
host = socket.gethostname()                           

port = 9999

# connection to hostname on the port.
server.connect((host, port))                               

# Receive no more than 1024 bytes
msg = server.recv(1024)
resp = "It's a pleasure"
server.send(resp.encode("ascii"))

server.close()
print (msg.decode('ascii'))
