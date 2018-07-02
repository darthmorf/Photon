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
