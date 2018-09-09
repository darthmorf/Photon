class Packet:
  def __init__(self, packetType):
    self.type = packetType

class LoginRequestPacket(Packet):
  def __init__(self, username, password):
    Packet.__init__(self, "LOGINREQUEST")
    self.username = username
    self.password = password

class LoginResponsePacket(Packet):
  def __init__(self, valid, err=""):
    Packet.__init__(self, "LOGINRESPONSE")
    self.valid = valid
    self.err = err

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
  def __init__(self, message, sender, timeSent):
    Packet.__init__(self, "MESSAGE")
    self.message = message
    self.sender = sender
    self.timeSent = timeSent

class MessageListPacket(Packet):
  def __init__(self, messageList):
    Packet.__init__(self, "MESSAGELIST")
    self.messageList = messageList

class UserListPacket(Packet):
  def __init__(self, userList):
    Packet.__init__(self, "USERLIST")
    self.userList = userList
