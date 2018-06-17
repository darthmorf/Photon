# Main Server file

import socket                                         
from threading import Thread
import pickle


# Global Variables

ClientCount = 0
Messages = ["<Server>: Hello", "<Server>: World"]
Clients  = []


# Classes

class Client:
  def __init__(self, clientId, clientSocket, clientAddress):
    global Messages
    self.id = clientId
    self.socket = clientSocket
    self.address = clientAddress

    print("Got a connection from " + str(self.address))
    self.socket.send(encode(Messages))

  def ListenForPackets(self):
    global Messages
    while True:
      message = decode(self.socket.recv(1024)) # Wait for message from client
      Messages.append(message)
      SendToClients(message)


# Functions

def SendToClients(message):
  global Clients
  for client in Clients:
    client.socket.send(encode(message))
    
# Dumps and Loads are not well named
def encode(packet):
  return pickle.dumps(packet)
def decode(packet):
  return pickle.loads(packet)

def __main__():
  # Create a socket object
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

  # Get local machine name and assign a port
  host = socket.gethostname()                           
  port = 9999                                           

  # Bind to the port
  serverSocket.bind((host, port))

  # Queue up to 5 requests
  serverSocket.listen(5)                                           
  print("\nListening for connections...")
   
  while True:
    global Clients
    global ClientCount
    # Wait for connections
    clientSocket, clientAddress = serverSocket.accept()
    newClient = Client(ClientCount, clientSocket, clientAddress)
    ClientCount += 1
    Clients.append(newClient)
    newThread = Thread(target=newClient.ListenForPackets)
    newThread.start()


if __name__ == "__main__":
   __main__()
