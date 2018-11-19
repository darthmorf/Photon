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

_messages = []
_clients  = []
_database = None

MAXTRANSMISSIONSIZE = 40960



# Classes

class Database:
  """
  Contains all methods relating to reading and writing from the database.

  Attributes:
    roConnection (sqlite3.Connection): The main read only database connection. Used for most get functions.
    roCursor  (sqlite3.Cursor): The cursor for the main read only connection.
    writeQueue (photonUtilities.CircularQueue): The queue used for database write commands in the dbWriter() method.
    writeThread (threading.Thread): The separate thread started for the database writer.

  ToDo:
    Get database file to load via parameter.
    Move to seperate file.
  """
  def __init__(self):
    """ Initialises the database by creating a read only connection and starting the asyncronous writer function """
    try:
      self.roConnection = sqlite3.connect("file:photon.db?mode=ro", uri=True) # Load database from file in read only mode
      self.roCursor = self.roConnection.cursor()
      self.writeQueue = CircularQueue(999)
      self.writeThread = Thread(target=self.dbWriter)
      self.writeThread.start()
    except Exception:
      ReportError()

    
  def dbWriter(self): 
    """
    Writes all SQL statements in the queue sequentially as writes to the database must be done one at a time.
    Should be run asynchronously.
    """
    try:
      global _messages
      while True:
        if not self.writeQueue.isEmpty():
          connection = sqlite3.connect("photon.db")
          cursor = connection.cursor()
          command = self.writeQueue.deQueue()
          cursor.execute(command[0], command[1]) # Execute SQL command
          connection.commit() # Save changes to DB
          cursor.execute("SELECT last_insert_rowid()")
          if len(command) == 4:
            _messages[command[3]].messageId = cursor.fetchall()[0][0]
          command[2].release()  # Release semaphore flag so the client thread can continue
          connection.close()
    except Exception:
      ReportError()


  def queryLogin(self, username, password):
    """
    Checks whether supplied login credenitals are valid.

    Args:
      username (string): the username of the user account to check.
      password (string): the password of the user account to check. Should be a hash of the password, not the plaintext.

    Returns:
      (bool): True if login successful, False if unsuccessful.
    """
    try:
      self.roCursor.execute("SELECT * FROM User")
      users = self.roCursor.fetchall()
      for user in users: # [0]: id [1]: name [2]: password [3]: admin
        if user[1] == username and user[2] == password:
          if user[3] == 1:
            return (True, user[0], True)
          else:
            return (True, user[0], False)
      return (False)
    except Exception:
      ReportError()


  def loadMessages(self, count=510): # Load last x messages from database
    """
    Loads the most recent messages from the database, and stores them globally.

    Args:
      count (int, optional): the amount of messages to load from the database.

    ToDo:
      return rather than store globally.
    """
    try:
        global _messages
        self.roCursor.execute("SELECT * FROM Message limit ? offset (SELECT count(*) FROM Message)-?", (str(count), str(count)))
        messages = self.roCursor.fetchall()
        for message in messages:
          self.roCursor.execute("SELECT name FROM User WHERE user_id == ?", (str(message[1]),))
          username = self.roCursor.fetchall()[0][0]
          constructedMessage = Message(messageId=message[0], senderId=message[1], senderName=username, contents=message[2], timeSent=message[3], recipientId=message[4], colour=message[5])
          _messages.append(constructedMessage)
    except Exception:
        ReportError()


  def userExists(self, username):
    """
    Check to see if a user with specific username exists.

    Args:
      username (string): the username of the user to lookup.

    Returns:
      (bool): True if the user exists, False if the user does not.
    """
    self.roCursor.execute("SELECT name FROM User WHERE name == ?", (username,))
    if len(self.roCursor.fetchall()) > 0:
      return True
    else:
      return False


  def listUsers(self):
    """
    Gets a list of all registered users

    Returns:
      (list of (int, string, bool)): Returns a list of tuples conaining the userId, username and whether they're admin.

    ToDo:
      Limit the amount of users that can be fetched at once.
    """
    connection = sqlite3.connect("file:photon.db?mode=ro", uri=True)
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, name, admin FROM User WHERE name != 'SERVER'")
    users = cursor.fetchall()
    return users
  

  def getUserDetails(self, user):
    """
    Gets the userId, message count, and reports for a specific user.

    Args:
      user (string): the username of the user who's info should be fetched.

    Returns:
      (int, int, list of (string, string, string, int)): The details of the user, corresponding to (user id, message count, list of (reported message, report reason, reporter name, reporter id).
    """
    try:
      connection = sqlite3.connect("file:photon.db?mode=ro", uri=True)
      cursor = connection.cursor()
      cursor.execute("SELECT user_id FROM User WHERE name == ?", (user,))
      userId = cursor.fetchall()[0][0]
      cursor.execute("SELECT count(*) FROM Message WHERE sender_id == ?", (userId,))
      messageCount = cursor.fetchall()[0][0]
      cursor.execute("SELECT * FROM Flag WHERE reportedUser_id == ?", (userId,))
      flagged = cursor.fetchall()
      flags = []
      for flag in flagged:
        cursor.execute("SELECT contents FROM Message WHERE message_id == ?", (flag[2],))
        message = cursor.fetchall()[0][0]
        cursor.execute("SELECT name FROM User WHERE user_id == ?", (flag[3],))      
        reporterName = cursor.fetchall()[0][0]
        flags.append((message, flag[4], reporterName, flag[3]))
                     
      return (userId, messageCount, flags)
    except Exception:
      ReportError()

  
  def addUser(self, username, password):
    """
    Creates a new user entry in the database.

    Args:
      username (string): the username of the account to create.
      password (string): the password of the account to create - this should be hashed.
    """
    semaphore = Semaphore(value=0) # Create a semaphore to be used to signal once the database write has been completed
    self.writeQueue.enQueue(("INSERT into User(name, password) values (?, ?)", (username, password), semaphore))
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete


  def addMessage(self, message):
    """
    Creates a new message entry in the database.

    Args:
      message (Message): The instance of message class containing the information that needs to be written.

    Returns:
      
    """
    global _messages
    semaphore = Semaphore(value=0) # Create a semaphore to be used to tell once the database write has been completed
    _messages.append(message)
    messageIndex = len(_messages) - 1
    self.writeQueue.enQueue(("INSERT into Message(sender_id, contents, timeSent, recipient_id, colour) values (?,?,?,?,?)", (str(message.senderId), message.contents, message.timeSent, message.recipientId, message.colour), semaphore, messageIndex))
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete
    return _messages[messageIndex] # Message object will have been updated with it's ID by the DB writer

  def addReport(self, messageId, reporterId, reportReason):
    connection = sqlite3.connect("file:photon.db?mode=ro", uri=True)
    cursor = connection.cursor()
    cursor.execute("SELECT sender_id FROM Message where message_id == ?", (messageId,))
    reportedUserId = cursor.fetchall()[0][0]
    semaphore = Semaphore(value=0) # Create a semaphore to be used to tell once the database write has been completed
    self.writeQueue.enQueue(("INSERT into Flag(reportedUser_id, message_id, reporter_id, reportReason) values (?,?,?,?)", (reportedUserId, messageId, reporterId, reportReason), semaphore))
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete

  def editMessage(self, messageId, newContent):
    semaphore = Semaphore(value=0) # Create a semaphore to be used to tell once the database write has been completed
    self.writeQueue.enQueue(("UPDATE Message SET contents=? WHERE message_id=?", (newContent, messageId), semaphore))
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete

  def deleteMessage(self, messageId):
    semaphore = Semaphore(value=0) # Create a semaphore to be used to tell once the database write has been completed
    self.writeQueue.enQueue(("UPDATE Message SET contents=?,sender_id=?,colour=? WHERE message_id=?", ("_message deleted_", 1, INFO, messageId), semaphore))
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete
    
class Client:
  """
  Represents one client that is connected to the server. A new instance is made for each connection, each client only interacts with their corresponding thread.

  Properties:
    socket (socket.socket): The websocket that this client is connected through.
    address (string): The IP of the connected client.
    id (int): the id of the connected client (not constant between sessions).
    thread (threading.thread): The asyncronous listener thread for this client.
    username (string): The username of the user.
    userid (int): The id of the user account (constant between sessions).
    admin (bool): Denotes whether the user account is admin.
  """
  def __init__(self, clientSocket, clientAddress):
    """
    Initialises the connection process, starts asynchronous listener thread and handles login handshake and account creation

    Args:
      clientSocket (socket.socket): the websocket that the connection is handled over.
      clientAddress (string, int): The IP and id of the connected client.

    ToDo:
      Break this up!
    """
    try:
      global _messages, _database, _clients
      self.socket = clientSocket
      self.address = clientAddress[0]
      self.id = clientAddress[1]
      self.thread = None
      self.username = "UNKNOWN"
      self.userid = ""
      self.admin = False
      _clients.append(self)

      print(f"Received a connection from {self.address}, id {self.id}")

      # Client Login
      loginInvalid = True
      while loginInvalid:
        loginRequestPacket = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait for client login packet TODO: time this out

        if loginRequestPacket.type == "CREATEUSER":

          usernameExists = _database.userExists(loginRequestPacket.username)

          if usernameExists:
            userRegistered = RegisterResponsePacket(False, "A user with that name already exists")

          else:
            _database.addUser(loginRequestPacket.username, loginRequestPacket.password)
            userRegistered = RegisterResponsePacket(True)

          self.socket.send(encode(userRegistered))
        
        elif loginRequestPacket.type == "LOGINREQUEST":
          err = "Incorrect username or password"
          for client in _clients:
            if client.username == loginRequestPacket.username:
              valid = False
              err = "That user is already logged in"
              break
            
          else:              
            ret = _database.queryLogin(loginRequestPacket.username, loginRequestPacket.password) # Query credentials against database
            valid = ret[0]
            
          if not valid:
            print(f"Invalid login from: {self.address}, id {self.id} - {err}")
            loginResponse = LoginResponsePacket(False, err) # Tell the client the login was invalid
            self.socket.send(encode(loginResponse))

          else:
            print(f"Valid login from: {self.address}, id {self.id}")
            loginResponse = LoginResponsePacket(True, userId=ret[1], admin=ret[2]) # Tell the client the login was valid
            self.socket.send(encode(loginResponse))
            self.userid = ret[1]
            self.username = loginRequestPacket.username
            self.admin = ret[2]
            loginInvalid = False
          
      readyToListenPacket = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait until the client is ready to receive packets

      # Get as many previous messages as possible that will fit into the max transmision size
      messagesToSend = []
      newMessagesToSend = []
      for message in reversed(_messages): # reversed as we want the latest messages
        if message.recipientId == 1 or message.senderId == self.userid or message.recipientId == self.userid:
          newMessagesToSend.append(message)
          if len(encode(newMessagesToSend)) >= MAXTRANSMISSIONSIZE - 200: # We need a buffer of ~200 as when we construct the class the encoded size increases
            newMessagesToSend = messagesToSend
            break
          else:
            messagesToSend = newMessagesToSend
      newMessageListPacket = MessageListPacket(reversed(messagesToSend)) # Send the client the previous messages
      self.socket.send(encode(newMessageListPacket))

      
      newMessage = generateJoinLeaveMessage("joined", self.username)
      newMessage = _database.addMessage(newMessage)
      announceUserPacket = MessagePacket(newMessage) # Client has joined message
      sendToClients(announceUserPacket)

      self.listenerThread = Thread(target=self.ListenForPackets) # Start thread to listen for packets from client
      self.listenerThread.start()

      sendOnlineUsersPacket() # Tell clients a new user has joined

    except ConnectionResetError: # Lost connection with client
      print(f"Lost connection with: {self.address}, id {self.id}; closing connection")
      
      self.socket.close() # Close socket
      for i in range(0, len(_clients)):
        if _clients[i].id == self.id:
          del _clients[i] # Delete class instance
          break

      if self.username != "UNKNOWN":
        newMessage = generateJoinLeaveMessage("left", self.username)
        newMessage = _database.addMessage(newMessage)
        announceUserPacket = MessagePacket(newMessage)
        sendToClients(announceUserPacket)
        sendOnlineUsersPacket() # Tell clients a user has left
          
      return # Return from thread
    except Exception:
      ReportError()


  def ListenForPackets(self):
    """
    Listens for all communication from client. Should be called asyncronously in it's own thread.

    ToDo:
    Break this up?
    """
    try:
      global _messages, _clients, _database
      while True:
        
        packet = decode(self.socket.recv(MAXTRANSMISSIONSIZE)) # Wait for message from client
        if packet.type == "MESSAGE":
          packet.message.timeSent = GetDateTime() # Update the message with the time it was received
          packet.message = _database.addMessage(packet.message)
          sendToClients(packet)

        elif packet.type == "COMMAND":
          command = packet.command
          args = packet.args
          success = False
          err = ""
          response = ""
          targetClient = self
          print(f"User {self.username}, {self.id} executed command {command} with args {args}")

          if command == "help":
            success = True
            response = ["!*Available Commands*!",
                        ("help","provides a list of available commands"),
                        ("ping","pings the server"),
                        ("whisper <user> <message>","sends a direct message to <user>"),
                        ("markup","displays balsamiq markup syntax")
                        ]

          elif command == "markup":
            success = True
            response = ["!*Markup Syntax*!",
                        "Formats can be combined and symbols can be escaped with '\\'",
                        ("bold", "*example*", "\*example*"),
                        ("italic", "_example_", "\_example_"),
                        ("strikethrough", "~example~", "\~example~"),
                        ("underline", "!example!", "\!example!")
                        ]
          
          elif command == "ping":
            success = True
            response = "Pong!"

          elif command == "whisper":
            targetName = args[0]
            del args[0]
            for client in _clients:
              if client.username == targetName:
                targetClient = client
                success = True
                message = "_ (Whisper) " + " ".join(args) + "_"
                response = formatUsername(self.username) + message
                newMessage = Message(self.userid, self.username, message, GetDateTime(), targetClient.userid, INFO)
                newMessage = _database.addMessage(newMessage)
                break
            else:
              err = f"Could not find user with name {targetName}"

          else:
            err = "Unrecognised command"

          response = CommandResponsePacket(command, success, err, response, GetDateTime())
          self.socket.send(encode(response))
          if targetClient != self:
            targetClient.socket.send(encode(response))

        elif packet.type == "REQUESTUSERLIST":
          userlist = _database.listUsers()
          self.socket.send(encode(UserListPacket(userlist)))

        elif packet.type == "REQUESTUSERINFO":
          userinfo = _database.getUserDetails(packet.user)
          userInfoPacket = UserInfoPacket(userinfo[0], userinfo[1], userinfo[2])
          self.socket.send(encode(userInfoPacket))

        elif packet.type == "REPORTPACKET":
          _database.addReport(packet.messageId, packet.reporterId, packet.reportReason)

        elif packet.type == "EDITMESSAGE":
          _database.editMessage(packet.messageId, packet.newContents)
          i = 0
          for message in _messages:
            if message.messageId == packet.messageId:
              _messages[i].contents = packet.newContents
              break
            i+=1            
          sendToClients(packet) # Tell clients that the message has been edited.

        elif packet.type == "DELETEMESSAGE":
          _database.deleteMessage(packet.messageId)
          i = 0
          for message in _messages:
            if message.messageId == packet.messageId:
              _messages[i].contents = "_message deleted_"
              _messages[i].senderId = 1
              _messages[i].senderName = "SERVER"
              _messages[i].colour = INFO
              break
            i+=1            
          sendToClients(packet) # Tell clients that the message has been deleted.

        else:
          print(f"Unknown packet received: {packet.type}")
          
    except ConnectionResetError: # Lost connection with client
      print(f"Lost connection with: {self.address}, id {self.id}; closing connection")
      
      self.socket.close() # Close socket
      for i in range(0, len(_clients)):
        if _clients[i].id == self.id:
          del _clients[i] # Delete class instance
          break

      newMessage = generateJoinLeaveMessage("left", self.username)
      newMessage = _database.addMessage(newMessage)
      announceUserPacket = MessagePacket(newMessage)
      sendToClients(announceUserPacket)
      sendOnlineUsersPacket() # Tell clients a user has left
      
    except Exception:
      ReportError()



# Functions

def sendToClients(packet):
  """
  Sends a packet to every connected client.

  Args:
    packet (packets.packet): The packet instance to send to the clients.
  """
  try:
    global _clients
    for client in _clients:
      client.socket.send(encode(packet))    
  except ConnectionResetError: # Client has lost connection
    pass    
  except Exception:
    ReportError()


def sendOnlineUsersPacket():
  """
  Constructs and sends a packet containing all users that are online.
  """
  try:
    global _clients
    users = []
    for client in _clients:
      users.append(client.username)
    users = StringListMergeSort(users)
    onlineUsersPacket = OnlineUsersPacket(users)
    sendToClients(onlineUsersPacket)
  except Exception:
    ReportError()


def __main__():
  """
  The main body of the program; it all starts here.
  Loads database, then listens for connections and assigns them new threads as they come in.
  """
  try:
    print("Loading Database...")
    global _database
    _database = Database()  
    _database.loadMessages()
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
      # Wait for connections
      clientSocket, clientAddress = serverSocket.accept()
      newClient = Client(clientSocket, clientAddress)
  except Exception:
    ReportError()



if __name__ == "__main__":
   __main__()
