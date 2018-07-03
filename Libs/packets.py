class Packet:
  def __init__(self, packetType):
    self.type = packetType

class LoginRequestPacket(Packet):
  def __init__(self, username, password):
    Packet.__init__(self, "LOGINREQUEST")
    self.username = username
    self.password = password

class LoginResponsePacket(Packet):
  def __init__(self, valid, errCode=0):
    Packet.__init__(self, "LOGINRESPONSE")
    self.valid = valid
    self.errCode = errCode

class ReadyToListenPacket(Packet):
  def __init__(self):
    Packet.__init__(self, "READTOLISTEN")

class MessagePacket(Packet):
  def __init__(self, message, sender):
    Packet.__init__(self, "MESSAGE")
    self.message = message
    self.sender = sender

class MessageListPacket(Packet):
  def __init__(self, messageList):
    Packet.__init__(self, "MESSAGELIST")
    self.messageList = messageList
