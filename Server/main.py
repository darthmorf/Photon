# Main Server file

import socket                                         
from threading import *
import select
import sqlite3
import re

# Load classes and functions from shared libs
import sys
sys.path.insert(0, '../Libs')
from packets import *
from photonUtilities import *



# Global Variables

Messages = []
Clients  = []
Database = None

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
      while True:
        if len(self.writeQueue) > 0:
          connection = sqlite3.connect("photon.db")
          cursor = connection.cursor()
          cursor.execute(self.writeQueue[0][0], self.writeQueue[0][1]) # Execute SQL command
          connection.commit() # Save changes to DB
          self.writeQueue[0][2].release()  # Release semaphore flag so the client thread can continue
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
        self.roCursor.execute("select * from Messages limit ? offset (select count(*) from Messages)-?", (str(lastX), str(lastX)))
        messages = self.roCursor.fetchall()
        for message in messages:
          self.roCursor.execute("SELECT name FROM Users WHERE id == ?", (str(message[1]),))
          username = self.roCursor.fetchall()[0][0]
          constructedMessage = Message(message[1], username, message[2], message[3], message[4], message[5])
          Messages.append(constructedMessage)
    except Exception:
        ReportError()


  def UserExists(self, username):
    self.roCursor.execute("SELECT name FROM Users WHERE name == ?", (username,))
    if len(self.roCursor.fetchall()) > 0:
      return True
    else:
      return False
  
  def AddUser(self, username, password):
    semaphore = Semaphore(value=0) # Create a semaphore to be used to tell once the database write has been completed
    self.writeQueue.append(("insert into Users(name, password) values (?, ?)", (username, password), semaphore))
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete


  def AddMessage(self, message):
    global Messages
    semaphore = Semaphore(value=0) # Create a semaphore to be used to tell once the database write has been completed
    Messages.append(message)
    self.writeQueue.append(("insert into Messages(senderId, message, timeSent, recipientId, colour) values (?,?,?,?,?)", (str(message.senderId), message.contents, message.timeSent, message.recipientId, message.colour), semaphore))
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

          usernameExists = Database.UserExists(loginRequestPacket.username)

          if usernameExists:
            userRegistered = RegisterResponsePacket(False, "A user with that name already exists")

          else:
            Database.AddUser(loginRequestPacket.username, loginRequestPacket.password)
            userRegistered = RegisterResponsePacket(True)

          self.socket.send(encode(userRegistered))
        
        elif loginRequestPacket.type == "LOGINREQUEST":
          err = "Incorrect username or password"
          for client in Clients:
            if client.username == loginRequestPacket.username:
              valid = False
              err = "That user is already logged in"
              break
            
          else:              
            ret = Database.QueryLogin(loginRequestPacket.username, loginRequestPacket.password) # Query credentials against database
            valid = ret[0]
            
          if not valid:
            print("Invalid login from: " + str(self.address) + ", id " + str(self.id) + " - " + err)
            loginResponse = LoginResponsePacket(False, err) # Tell the client the login was invalid
            self.socket.send(encode(loginResponse))

          else:
            print("Valid login from: " + str(self.address) + ", id " + str(self.id))
            loginResponse = LoginResponsePacket(True, userId=ret[1]) # Tell the client the login was valid
            self.socket.send(encode(loginResponse))
            self.userid = ret[1]
            self.username = loginRequestPacket.username
            loginInvalid = False
          
      readyToListenPacket = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait until the client is ready to receive packets

      # Get as many previous messages as possible that will fit into the max transmision size
      messagesToSend = []
      newMessagesToSend = []
      for message in reversed(Messages): # reversed as we want the latest messages
        if message.recipientId == 1 or message.senderId == self.userid or message.recipientId == self.userid:
          newMessagesToSend.append(message)
          if len(encode(newMessagesToSend)) >= MAXTRANSMISSIONSIZE - 200: # We need a buffer of ~200 as when we construct the class the encoded size increases
            newMessagesToSend = messagesToSend
            break
          else:
            messagesToSend = newMessagesToSend
      newMessageListPacket = MessageListPacket(reversed(messagesToSend)) # Send the client the previous messages
      self.socket.send(encode(newMessageListPacket))

      
      newMessage = Message(1, "SERVER", " --- " + self.username + " has joined the server ---", GetDateTime())
      announceUserPacket = MessagePacket(newMessage) # Client has joined message
      Database.AddMessage(newMessage)
      SendToClients(announceUserPacket)

      self.listenerThread = Thread(target=self.ListenForPackets) # Start thread to listen for packets from client
      self.listenerThread.start()

      SendUserListPacket() # Tell clients a new user has joined

    except ConnectionResetError: # Lost connection with client
      print("Lost connection with: " + str(self.address) + ", id " + str(self.id) + "; closing connection")
      
      self.socket.close() # Close socket
      for i in range(0, len(Clients)):
        if Clients[i].id == self.id:
          del Clients[i] # Delete class instance
          break

      if self.username != "UNKNOWN":
        newMessage = Message(1, "SERVER", " --- " + self.username + " has left the server ---", GetDateTime())
        announceUserPacket = MessagePacket(newMessage)
        Database.AddMessage(newMessage)
        SendToClients(announceUserPacket)
        SendUserListPacket() # Tell clients a user has left
          
      return # Return from thread
    except Exception:
      ReportError()


  def ListenForPackets(self):
    try:
      global Messages, Clients, Database
      while True:
        
        packet = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait for message from client
        if packet.type == "MESSAGE":
          packet.message.timeSent = GetDateTime() # Update the message with the time it was received
          Database.AddMessage(packet.message)
          SendToClients(packet)

        elif packet.type == "COMMAND":
          command = packet.command
          args = packet.args
          success = False
          err = ""
          response = ""
          targetClient = self
          print("User " + self.username + ", " + str(self.id) + " executed command " + command + " with args " + str(args))
          
          if command == "ping":
            success = True
            response = "Pong!"

          if command == "whisper":
            targetName = args[0]
            del args[0]
            for client in Clients:
              if client.username == targetName:
                targetClient = client
                success = True
                message = "_ (Whisper) " + " ".join(args) + "_"
                response = formatUsername(self.username) + message
                newMessage = Message(self.userid, self.username, message, GetDateTime(), targetClient.userid, WHISPER)
                Database.AddMessage(newMessage)
                break
            else:
              err = "Could not find user with name " + targetName

          else:
            err = "Unrecognised command"

          response = CommandResponsePacket(command, success, err, response, GetDateTime())
          self.socket.send(encode(response))
          if targetClient != self:
            targetClient.socket.send(encode(response))
          
    except ConnectionResetError: # Lost connection with client
      print("Lost connection with: " + str(self.address) + ", id " + str(self.id) + "; closing connection")
      
      self.socket.close() # Close socket
      for i in range(0, len(Clients)):
        if Clients[i].id == self.id:
          del Clients[i] # Delete class instance
          break

      newMessage = Message(1, "SERVER", " --- " + self.username + " has left the server ---", GetDateTime())
      announceUserPacket = MessagePacket(newMessage)
      Database.AddMessage(newMessage)
      SendToClients(announceUserPacket)
      SendUserListPacket() # Tell clients a user has left
      
    except Exception:
      ReportError()



# Functions

def SendToClients(packet):
  try:
    global Clients
    for client in Clients:
      client.socket.send(encode(packet))    
  except ConnectionResetError: # Client has lost connection
    pass    
  except Exception:
    ReportError()


def SendUserListPacket():
  try:
    global Clients
    users = []
    for client in Clients:
      users.append(client.username)
    users.sort()
    userListPacket = UserListPacket(users)
    SendToClients(userListPacket)
  except Exception:
    ReportError()


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
