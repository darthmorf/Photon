import pickle
import traceback
import datetime


class Message():
  def __init__(self, senderId, senderName, contents, timeSent="", recipientId=1, colour="#000000"):
    self.senderId = senderId
    self.senderName = senderName
    self.contents = contents
    self.timeSent = timeSent
    self.recipientId = recipientId
    self.colour = colour


def HashString(string):  
  bitValueChunk = ""
  bitSum = 0

  for char in string:
    bitSum += ord(char)
    bitValue = format(ord(char), 'b') # Convert char to binary
    bitValueChunk += bitValue # Apend to 'binary chunk'

  n = 9
  bitValues = [bitValueChunk[i:i+n] for i in range(0, len(bitValueChunk), n)] # Split 'binary chunk' into list of 9 bit binary numbers

  moddedBitChunk = ""
  for bitValue in bitValues:
    bitValue = int(bitValue)
    moddedBitValue = bitValue + (bitValue % 37) # Modulo is a one way function, so we modulo by a prime as the core of the hash. This is the step that ensures the hash is unidirectional
    moddedBitValue = moddedBitValue * bitSum # Multiply by sum of the ascii values of the chars to ensure similar input strings look different
    moddedBitChunk += format(moddedBitValue, 'b') # Convert into binary again

  n = 6 # 6 bit chunks to avoid strange characters
  moddedBitValues = [moddedBitChunk[i:i+n] for i in range(0, len(moddedBitChunk), n)] # Split modded 'binary chunk' into list of 8 bit binary numbers    
  
  hashed = ""
  for moddedBitValue in moddedBitValues:
    hashed += chr(int(moddedBitValue, 2) + 33) # Convert binary value into decimal value then into the corresponding character, skipping the first 33 as they are non-printing/whitespace

  return hashed


def ReportError():
  traceback.print_exc()


def GetDateTime():
  return datetime.datetime.now().strftime("%y-%m-%d %H:%M") 


def formatUsername(name):
  return "[" + name + "]: "


def formatDateTime(time):
  return "" + time + " | "


# Dumps and Loads are not well named
def encode(packet):
  return pickle.dumps(packet)
def decode(packet):
  return pickle.loads(packet)
