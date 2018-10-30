class Packet:
  def __init__(self, packetType):
    self.type = packetType

class LoginRequestPacket(Packet):
  def __init__(self, username, password):
    Packet.__init__(self, "LOGINREQUEST")
    self.username = username
    self.password = password

class LoginResponsePacket(Packet):
  def __init__(self, valid, userId="", err="", admin=False):
    Packet.__init__(self, "LOGINRESPONSE")
    self.valid = valid
    self.err = err
    self.id = userId
    self.admin = admin

class RegisterPacket(Packet):
  def __init__(self, username, password):
    Packet.__init__(self, "CREATEUSER")
    self.username = username
    self.password = password

class RegisterResponsePacket(Packet):
  def __init__(self, valid, err=""):
    Packet.__init__(self, "REGISTERRESPONSE")
    self.valid = valid
    self.err = err
    
class MessagePacket(Packet):
  def __init__(self, message):
    Packet.__init__(self, "MESSAGE")
    self.message = message # Utilises Message class TODO just use message class

class MessageListPacket(Packet):
  def __init__(self, messageList):
    Packet.__init__(self, "MESSAGELIST")
    self.messageList = messageList

class OnlineUsersPacket(Packet):
  def __init__(self, userList):
    Packet.__init__(self, "ONLINEUSERS")
    self.userList = userList

class UserListPacket(Packet):
  def __init__(self, userList):
    Packet.__init__(self, "USERLIST")
    self.userList = userList

class CommandPacket(Packet):
  def __init__(self, command, args=[]):
    Packet.__init__(self, "COMMAND")
    self.command = command
    self.args = args

class CommandResponsePacket(Packet):
  def __init__(self, command, success, err="", response="", timeSent=""):
    Packet.__init__(self, "COMMANDRESPONSE")
    self.command = command
    self.success = success
    self.err = err
    self.response = response
    self.timeSent = timeSent
