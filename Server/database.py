
import sqlite3                            
from threading import *

# Load classes and functions from shared libs
import sys
sys.path.insert(0, '../Libs')
from packets import *
from photonUtilities import *

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
      self.messages = self.loadMessages()
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
      while True:
        if not self.writeQueue.isEmpty():
          connection = sqlite3.connect("photon.db")
          cursor = connection.cursor()
          command = self.writeQueue.deQueue()
          cursor.execute(command[0], command[1]) # Execute SQL command
          connection.commit() # Save changes to DB
          cursor.execute("SELECT last_insert_rowid()")
          if len(command) == 4:
            self.messages[command[3]].messageId = cursor.fetchall()[0][0]
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
    """
    try:
        constructedMessages = []
        self.roCursor.execute("SELECT * FROM Message limit ? offset (SELECT count(*) FROM Message)-?", (str(count), str(count)))
        messages = self.roCursor.fetchall()
        for message in messages:
          self.roCursor.execute("SELECT name FROM User WHERE user_id == ?", (str(message[1]),))
          username = self.roCursor.fetchall()[0][0]
          constructedMessage = Message(messageId=message[0], senderId=message[1], senderName=username, contents=message[2], timeSent=message[3], recipientId=message[4], colour=message[5])
          constructedMessages.append(constructedMessage)
        return constructedMessages
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
    Gets the userId, message count, admin and reports for a specific user.

    Args:
      user (string): the username of the user who's info should be fetched.

    Returns:
      (int, int, bool list of (string, string, string, int)): The details of the user, corresponding to (user id, message count, whether admin, list of (reported message, report reason, reporter name, reporter id).
    """
    try:
      connection = sqlite3.connect("file:photon.db?mode=ro", uri=True)
      cursor = connection.cursor()
      cursor.execute("SELECT user_id, admin FROM User WHERE name == ?", (user,))
      ret = cursor.fetchall()[0]
      userId = ret[0]
      admin = bool(ret[1])
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
                     
      return (userId, messageCount, admin, flags)
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
    semaphore = Semaphore(value=0) # Create a semaphore to be used to tell once the database write has been completed
    self.messages.append(message)
    messageIndex = len(self.messages) - 1
    self.writeQueue.enQueue(("INSERT into Message(sender_id, contents, timeSent, recipient_id, colour) values (?,?,?,?,?)", (str(message.senderId), message.contents, message.timeSent, message.recipientId, message.colour), semaphore, messageIndex))
    semaphore.acquire() # Wait until semaphore has been released IE has db write is complete
    return self.messages[messageIndex] # Message object will have been updated with it's ID by the DB writer

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