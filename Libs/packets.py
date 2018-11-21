class Packet:
  """
  Base packet class. Can be used to signal something without the need to transfer dataself.

  Args:
    packetType (string): An identifier to determine what the packet denotes. Should be all caps.
  """
  def __init__(self, packetType):
    self.type = packetType

class LoginRequestPacket(Packet):
  """
  Sends login details to the server. 

  Args:
    username (string): The username to login with.
    password (string): The password to login with. Should be hashed.
  """
  def __init__(self, username, password):
    Packet.__init__(self, "LOGINREQUEST")
    self.username = username
    self.password = password

class LoginResponsePacket(Packet):
  """
  Sends login response to client.

  Args:
    valid (bool): Whether the login was successful.
    err (string, optional): Why the login was not successful.
    id (int, optional): The user id of the account, if successfully logged in.
    admin (bool, optional): Whether the user account is an admin.
  """
  def __init__(self, valid, userId="", err="", admin=False):
    Packet.__init__(self, "LOGINRESPONSE")
    self.valid = valid
    self.err = err
    self.id = userId
    self.admin = admin

class RegisterPacket(Packet):
  """
  Asks the server to create a user account.
  Args:
    username (string): The username of the account to create.
    password (string): The password of the account to create. Should be hashed.
  """
  def __init__(self, username, password):
    Packet.__init__(self, "CREATEUSER")
    self.username = username
    self.password = password

class RegisterResponsePacket(Packet):
  """
  Informs the client if the account was created succesfully.

  Args:
    valid (bool): Whether the account creation was a success.
    err (string, optional): The reason why the account creation was not a success.
  """
  def __init__(self, valid, err=""):
    Packet.__init__(self, "REGISTERRESPONSE")
    self.valid = valid
    self.err = err
    
class MessagePacket(Packet):
  """
  Sends a message to the client or the server.

  Args:
    message (photonUtilities.Message): The message to send.
  """
  def __init__(self, message):
    Packet.__init__(self, "MESSAGE")
    self.message = message # Utilises Message class

class MessageListPacket(Packet):
  """
  Sends multiple messages to the client or server.

  Args:
    messageList (list of photonUtilities.Message): The list of messages to send.
  """
  def __init__(self, messageList):
    Packet.__init__(self, "MESSAGELIST")
    self.messageList = messageList

class OnlineUsersPacket(Packet):
  """
  Sends a list of the usernames of all clients which are online.

  Args:
    userList (list of string): List of usernames of online clients.
  """
  def __init__(self, userList):
    Packet.__init__(self, "ONLINEUSERS")
    self.userList = userList

class UserListPacket(Packet):
  """
  Sends a list of all users registered.

  Args:
    userList (list of (int, string, bool)): A list of tuples conaining the userId, username and whether they're admin.
  """
  def __init__(self, userList):
    Packet.__init__(self, "USERLIST")
    self.userList = userList

class RequestUserInfoPacket(Packet):
  """
  Requests details about a specific user.

  Args:
    user (string): The username of the user to get the info of.
  """
  def __init__(self, user):
    Packet.__init__(self, "REQUESTUSERINFO")
    self.user = user

class UserInfoPacket(Packet):
  """
  Sends information about a specific user.

  Args:
    id (int): The id of the user
    messageCount (int): The number of messages sent by the user.
    admin (bool): Whether the user is an admin.
    flags (list of (string, string, string, int): Contains info about reports for that user, corresponding to list of (reported message, report reason, reporter name, reporter id).
  """
  def __init__(self, id, messageCount, admin, flags):
    Packet.__init__(self, "USERINFO")
    self.id = id
    self.messageCount = messageCount
    self.admin = admin
    self.flags = flags

class CommandPacket(Packet):
  """
  Contains information about an executed command

  Args:
    command (string): The command that was executed.
    args (list of string): A list of the arguments supplied to the command.
  """
  def __init__(self, command, args=[]):
    Packet.__init__(self, "COMMAND")
    self.command = command
    self.args = args

class CommandResponsePacket(Packet):
  """
  Contains information about the execution of a command.

  Args:
    command (string): The command that was executed.
    success (bool): Whether the command was executed successfully.
    err (string, optional): The reason why the command could not execute.
    response (string, optional): The response of the command.
    timeSent (string, optional): The time that the command was executed.
  """
  def __init__(self, command, success, err="", response="", timeSent=""):
    Packet.__init__(self, "COMMANDRESPONSE")
    self.command = command
    self.success = success
    self.err = err
    self.response = response
    self.timeSent = timeSent

class ReportPacket(Packet):
  """
  Tells the server to flag a message.

  Args:
    messageId (int): The id of the reported message.
    reporterId (int): The id of the user who reported the message.
    reportReason (string): The reason that the message was flagged.
  """
  def __init__(self, messageId, reporterId, reportReason):
    Packet.__init__(self, "REPORTPACKET")
    self.messageId = messageId
    self.reporterId = reporterId
    self.reportReason = reportReason

class DeleteMessagePacket(Packet):
  def __init__(self, messageId):
    Packet.__init__(self, "DELETEMESSAGE")
    self.messageId = messageId

class EditMessagePacket(Packet):
  def __init__(self, messageId, newContents):
    Packet.__init__(self, "EDITMESSAGE")
    self.messageId = messageId
    self.newContents = newContents

class SetAdminStatusPacket(Packet):
  def __init__(self, admin, userId):
    Packet.__init__(self, "SETADMINSTATUS")
    self.userId = userId
    self.admin = admin