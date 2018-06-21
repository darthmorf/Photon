# Main Server file

import socket                                         
from threading import *
import pickle
import traceback
import select


# Global Variables

Messages = [["Server","Hello"], ["Server","World"]]
Clients  = []


# Classes

class Packet:
  def __init__(self, packetType):
    self.type = packetType

class ClientHandshakePacket(Packet):
  def __init__(self, username):
    Packet.__init__(self, "CLIENTHANDSHAKE")
    self.username = username

class PingPacket(Packet):
  def __init__(self, response):
    Packet.__init__(self, "PING")
    self.response = response

class MessagePacket(Packet):
  def __init__(self, message, sender):
    Packet.__init__(self, "MESSAGE")
    self.message = message
    self.sender = sender

class MessageListPacket(Packet):
  def __init__(self, messageList):
    Packet.__init__(self, "MESSAGELIST")
    self.messageList = messageList
    
  
class Client:
  def __init__(self, clientSocket, clientAddress):
    try:
      global Messages
      self.socket = clientSocket
      self.address = clientAddress[0]
      self.id = clientAddress[1]
      self.thread = None
      self.username = "UNKNOWN"

      print("Got a connection from " + str(self.address) + ", id " + str(self.id))

      handshakePacket = decode(self.socket.recv(1024)) # Wait for client handshake TODO: time this out
      self.username = handshakePacket.username

      newMessageListPacket = MessageListPacket(Messages)
      self.socket.send(encode(newMessageListPacket))
      
      self.listenerThread = Thread(target=self.ListenForPackets)
      self.listenerThread.start()
     
    except Exception:
      ReportError()

  def ListenForPackets(self):
    try:
      global Messages
      while True:
        
        packet = decode(self.socket.recv(1024)) # Wait for message from client
        if packet.type == "PING": # Ping response from client
          if packet.response == True:
            print("pong") #TODO do stuff
          elif packet.response == False: # Ping is not a response; the client wants a response
            newPingPacket = PingPacket(True) 
            self.socket.send(encode(newPingPacket))

        elif packet.type == "MESSAGE":
          Messages.append([packet.sender, packet.message])
          SendToClients(packet)

    except ConnectionResetError: # Lost connection with client
      
      print("Lost connection with: " + str(self.address) + ", id " + str(self.id) + "; closing connection")
      self.socket.close() # Close socket
      global Clients
      for i in range(0, len(Clients)):
        if Clients[i].id == self.id:
          del Clients[i] # Delete class instance
          
      return # Return from Listen thread
      
    except Exception:
      ReportError()


# Functions

def ReportError():
  traceback.print_exc()

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
    newClient = Client(clientSocket, clientAddress)
    Clients.append(newClient)


if __name__ == "__main__":
   __main__()
