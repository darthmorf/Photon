# Main Server file

import socket                                         
from threading import *
import pickle
import traceback
import select
import sqlite3

# Load packet classes from shared libs
import sys
sys.path.insert(0, '../Libs')
from packets import *



# Global Variables

Messages = []
Clients  = []
Database = ""

MAXTRANSMISSIONSIZE = 4096



# Classes

class DataBase:
  def __init__(self):
    try:
      self.roConnection = sqlite3.connect("file:photon.db?mode=ro", uri=True) # Load database from file in read only mode
      self.roCursor = self.roConnection.cursor()
      self.writeQueue = []
      self.writeThread = Thread(target=self.DbWriter)
      self.writeThread.start()
    except Exception:
      ReportError()

    
  def DbWriter(self): # All writes to the database done from one thread and queued
    try:
      connection = sqlite3.connect("photon.db")
      cursor = connection.cursor()
      while True:
        if len(self.writeQueue) > 0:
          self.writeQueue[0][1].acquire() # Aquire semaphore so that the thread that created it's acquire() call will be blocking
          cursor.execute(self.writeQueue[0][0]) # Execute SQL command
          connection.commit() # Save changes to DB
          self.writeQueue[0][1].release()  # Release semaphore flag so the client thread can continue
          del self.writeQueue[0]
        connection.close()
    except Exception:
      ReportError()


  def QueryLogin(self, username, password): # Return true if username & password are valid
    try:
      self.roCursor.execute("select * from Users")
      users = self.roCursor.fetchall()
      for user in users: # [0]: id [1]: name [2]: password
        if user[1] == username and user[2] == password:
          return [True, user[0]]
      return [False]
    except Exception:
      ReportError()


  def LoadMessages(self): # Load last x messages from database
    try:
        global Messages
        lastX = 510
        self.roCursor.execute("select * from Messages limit " + str(lastX) + " offset (select count(*) from Messages)-" + str(lastX))
        messages = self.roCursor.fetchall()
        for message in messages:
          self.roCursor.execute("SELECT name FROM Users WHERE id == " + str(message[1]))
          username = self.roCursor.fetchall()[0][0]
          Messages.append([username, message[2]])
    except Exception:
        ReportError()

  
  def AddUser(self, username, password):
    semaphore = Semaphore() # Create a semaphore to be used to tell once the database write has been completed
    self.writeQueue.append(["insert into Users(name, password) values ('" + username + "', '" + password + "')", semaphore])
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete


  def AddMessage(self, userid, username, message):
    global Messages
    semaphore = Semaphore() # Create a semaphore to be used to tell once the database write has been completed
    Messages.append([username, message]) 
    self.writeQueue.append(["insert into Messages(senderId, message) values ('" + str(userid) + "', '" + message + "')", semaphore])
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete


class Client:
  def __init__(self, clientSocket, clientAddress):
    try:
      global Messages
      global Database
      global Clients
      self.socket = clientSocket
      self.address = clientAddress[0]
      self.id = clientAddress[1]
      self.thread = None
      self.username = "UNKNOWN"
      self.userid = ""
      Clients.append(self)

      print("Received a connection from " + str(self.address) + ", id " + str(self.id))

      # Client Login
      loginInvalid = True
      while loginInvalid:
        loginRequestPacket = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait for client login packet TODO: time this out

        if loginRequestPacket.type == "CREATEUSER":
          Database.AddUser(loginRequestPacket.username, loginRequestPacket.password)
          userRegistered = Packet("REGISTERDONE")
          self.socket.send(encode(Packet))
        
        else:
          self.username = loginRequestPacket.username
          ret = Database.QueryLogin(loginRequestPacket.username, loginRequestPacket.password) # Query credentials against database
          valid = ret[0]
          
          if not valid:
            print("Invalid login from: " + str(self.address) + ", id " + str(self.id))
            loginResponse = LoginResponsePacket(False) # Tell the client the login was invalid
            self.socket.send(encode(loginResponse))

          else:
            print("Valid login from: " + str(self.address) + ", id " + str(self.id))
            loginResponse = LoginResponsePacket(True) # Tell the client the login was valid
            self.socket.send(encode(loginResponse))
            self.userid = ret[1]
            loginInvalid = False
          
      readyToListenPacket = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait until the client is ready to receive packets

      # Get as many previous messages as possible that will fit into the max transmision size
      messagesToSend = []
      newMessagesToSend = []
      for message in reversed(Messages): # reversed as we want the latest messages
        newMessagesToSend.append(message)
        if len(encode(newMessagesToSend)) >= MAXTRANSMISSIONSIZE - 200: # We need a buffer of ~200 as when we construct the class the encoded size increases
          newMessagesToSend = messagesToSend
          break
        else:
          messagesToSend = newMessagesToSend
      newMessageListPacket = MessageListPacket(reversed(messagesToSend)) # Send the client the previous messages
      self.socket.send(encode(newMessageListPacket))
      
      announceUserPacket = MessagePacket(" --- " + self.username + " has joined the server ---", "SERVER") # Client has joined message
      Database.AddMessage(1, announceUserPacket.sender, announceUserPacket.message)
      SendToClients(announceUserPacket)

      self.listenerThread = Thread(target=self.ListenForPackets) # Start thread to listen for packets from client
      self.listenerThread.start()

    except ConnectionResetError: # Lost connection with client
      print("Lost connection with: " + str(self.address) + ", id " + str(self.id) + "; closing connection")
      
      self.socket.close() # Close socket
      for i in range(0, len(Clients)):
        if Clients[i].id == self.id:
          del Clients[i] # Delete class instance
          break

      announceUserPacket = MessagePacket(" --- " + self.username + " has left the server ---", "SERVER")
      Database.AddMessage(1, announceUserPacket.sender, announceUserPacket.message)
      SendToClients(announceUserPacket)
          
      return # Return from thread
    except Exception:
      ReportError()


  def ListenForPackets(self):
    try:
      global Messages
      while True:
        
        packet = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait for message from client
        if packet.type == "MESSAGE":
          Database.AddMessage(self.userid, packet.sender, packet.message)
          SendToClients(packet)
          
    except ConnectionResetError: # Lost connection with client
      print("Lost connection with: " + str(self.address) + ", id " + str(self.id) + "; closing connection")
      
      self.socket.close() # Close socket
      global Clients
      for i in range(0, len(Clients)):
        if Clients[i].id == self.id:
          del Clients[i] # Delete class instance
          break

      announceUserPacket = MessagePacket(" --- " + self.username + " has left the server ---", "SERVER")
      Database.AddMessage(1, announceUserPacket.sender, announceUserPacket.message)
      SendToClients(announceUserPacket)
      
    except Exception:
      ReportError()



# Functions

def ReportError():
  traceback.print_exc()


def SendToClients(packet):
  try:
    global Clients
    for client in Clients:
      client.socket.send(encode(packet))    
  except ConnectionResetError: # Client has lost connection
    pass    
  except Exception:
    ReportError()

    
# Dumps and Loads are not well named
def encode(packet):
  return pickle.dumps(packet)
def decode(packet):
  return pickle.loads(packet)


def __main__():
  try:
    print("Loading Database...")
    global Database
    Database = DataBase()  
    Database.LoadMessages()
    # Create a socket object
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    # Get local machine name and assign a port
    host = socket.gethostname()                           
    port = 9998                                 

    # Bind to the port
    serverSocket.bind((host, port))

    # Queue up to 5 requests
    serverSocket.listen(5)                                           
    print("Listening for connections...")
     
    while True:
      global Clients
      global ClientCount
      # Wait for connections
      clientSocket, clientAddress = serverSocket.accept()
      newClient = Client(clientSocket, clientAddress)
  except Exception:
    ReportError()



if __name__ == "__main__":
   __main__()
