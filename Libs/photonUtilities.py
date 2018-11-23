import pickle
import traceback
import datetime

# Global Colours
BLACK = "#000000"
COMMANDERROR = "#ff3030"
INFO = "#636363"


class CircularQueue():
  """
  A custom circular queue implementation.
  """
  def __init__(self, maxSize):
    if maxSize < 1:
      raise ValueError("Queue size must be at least 1")
    self.data = [''] * maxSize
    self.rear = -1
    self.front= 0
    self.size = 0
    self.maxSize = maxSize

  def enQueue(self, item):
    """
    Add an item to the queue.

    Args:
      item (*): Item to add to the queue.
    """
    if self.size == self.maxSize:
      raise ValueError("Cannot enqueue when the queue is full")
    else:
      self.rear = (self.rear + 1) % self.maxSize
      self.data[self.rear] = item
      self.size = self.size + 1

  def deQueue(self):
    """
    Removes an item from the queue.

    Returns:
      (*): The item at the front of the queue.
    """
    self.front += 1
    self.size -= 1
    return self.data[self.front-1]

  def isFull(self):
    """ Determines if the queue is full. """
    return self.size == self.rear

  def isEmpty(self):
    """ Determines if the queue is empty. """
    return self.size == 0


class Message():
  """
  Represents a message.

  Args:
    senderId (int): The user id of the message sender.
    senderName (string, optional): The username of the
    contents (string, optional): The actual message content
    timeSent (string, optional): The time that the message was sent.
    recipientId (int, optional): The user id of the user that sent the message.
    colour (string, optional): The colour to display the message as.
    messageId (int, optional): The id of the message.
  """
  def __init__(self, senderId="", senderName="", contents="", timeSent="", recipientId=1, colour="#000000", messageId=""):
    self.senderId = senderId
    self.senderName = senderName
    self.contents = contents
    self.timeSent = timeSent
    self.recipientId = recipientId
    self.colour = colour
    self.messageId = messageId


def hashString(string): 
  """
  Custom implementation of a simple one way hashing algorithm

  Args:
    string (string): The string to hash.

  Returns:
    (string): The hashed string.
  """ 
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


def integerMergeSort(mergelist):
  """
  Custom implementation of a mergesort algorithm for integers.

  Args:
    mergeList (list of int): The list to sort.

  Returns:
    (list of int): The sorted list.
  """
  if len(mergelist) > 1:
      mid = len(mergelist) // 2 # Perform integer division
      lefthalf = mergelist[:mid] # Left half of merglist into lefthalf
      righthalf = mergelist[mid:] # Right half of merglist into righthalf
      lefthalf = MergeSort(lefthalf)
      righthalf = MergeSort(righthalf)

      i = 0
      j = 0
      k = 0
      while i < len(lefthalf) and j < len(righthalf):
          if lefthalf[i] < righthalf[j]:
              mergelist[k] = lefthalf[i]
              i += 1
          else:
              mergelist[k] = righthalf[j]
              j += 1
          k += 1

      # Check if left half has elements not merged
      while i < len(lefthalf):
          mergelist[k] = lefthalf[i] # If so, add to mergelist
          i += 1
          k += 1
      # Check if right half has elements not merged
      while j < len(righthalf):
          mergelist[k] = righthalf[j] # If so, add to mergelist
          j += 1
          k += 1
  return mergelist


def stringListMergeSort(mergelist):
  """
  Custom implementation of a mergesort algorithm for strings.

  Args:
    mergeList (list of string): The list to sort.

  Returns:
    (list of string): The sorted list.
  """
  if len(mergelist) > 1:
    mid = len(mergelist) // 2 # Perform integer division
    lefthalf = mergelist[:mid] # Left half of merglist into lefthalf
    righthalf = mergelist[mid:] # Right half of merglist into righthalf
    lefthalf = StringListMergeSort(lefthalf)
    righthalf = StringListMergeSort(righthalf)

    i = 0
    j = 0
    k = 0
    while i < len(lefthalf) and j < len(righthalf):
        l = 0
        while ord(lefthalf[i][l]) == ord(righthalf[j][l]) and l < len(lefthalf[i])-1 and l < len(righthalf[j])-1: # If the charachers are the same, we must look at the next one until the end
            l += 1
        if ord(lefthalf[i][l]) < ord(righthalf[j][l]):
            mergelist[k] = lefthalf[i]
            i += 1
        else:
            mergelist[k] = righthalf[j]
            j += 1
        k += 1

    # Check if left half has elements not merged
    while i < len(lefthalf):
        mergelist[k] = lefthalf[i] # If so, add to mergelist
        i += 1
        k += 1
    # Check if right half has elements not merged
    while j < len(righthalf):
        mergelist[k] = righthalf[j] # If so, add to mergelist
        j += 1
        k += 1
  return mergelist


def reportError():
  """ Easier name for traceback.print_exc(). """
  traceback.print_exc()


def getDateTime():
  """ Gets the current time in yy/mm/dd HH:MM format. """
  return datetime.datetime.now().strftime("%y-%m-%d %H:%M") 


def formatUsername(name):
  """ 
  Formats a string to confirm with username display style.

  Args:
    name (string): The name to format.

  Returns:
    (string): The formatted string.
  """
  if name == "" or name == "SERVER":
    return ""
  else:
    return "<" + name + ">: "


def formatDateTime(time):
  """
  Formats a string to confirm with time display style.

  Args:
    time (string): The time to format.

  Returns:
    (string): The formatted string.
  """
  if time == "":
    return ""
  else:
    return "" + time + " | "


def generateJoinLeaveMessage(direction, username):
  """
  Generates a standard message notifying of when users join/leave the server.

  Args:
    direction (string): Contains whether the user 'joined' or 'left' the server.
    username (string): The user who joined or left.

  Returns:
    (Message): The generated message.
  """
  return Message(1, "SERVER", "_" + username + " has " + direction + " the server_", getDateTime(), colour=INFO)


def debugPrint(message, debug):
  """
  Conditional Print depending on whether launched in debug mode or not.

  Args:
    message (string): The message to print.
    debug (bool): Whether the message should be printed.
  """
  if debug:
    print(message)


def encode(packet):
  """ Better name for pickle.dumps() """
  return pickle.dumps(packet)
def decode(packet):
  """ Better name for pickle.loads() """
  return pickle.loads(packet)
