# Main Client File

from tkinter import *
from tkinter import ttk
import socket
import pickle                                    
from threading import Thread
import traceback
import atexit
import os
import re

# Global vars

ServerSocket = None
Username = ""

NONPRINTINGCHAR = '\u200B' # Used to replace a character in a string whilst keeping indexes the same

# Classes

class UserInterface:
  def __init__(self, master):
    try:
      self.master = master
      self.master.title("Photon - IM Client")
      self.master.iconbitmap(r".\icon.ico")

      self.master.geometry('1032x516') #Create a new window with resolution 1280x720 (scalable)
      self.master.resizable(False, False)
      
      self.messageDisplay = Text(master, height=28, width=145, relief="groove", state="disabled", font=("Consolas", 10))
      self.messageDisplay.grid(column=0, columnspan=2, padx=2, pady=2, row=1) #Set the messageDisplay to expand dynamically

      self.messageInput = ttk.Entry(master, justify="left", takefocus="true", width=150)
      self.messageInput.grid(column=0, padx=2, pady=6, row=2)

      self.sendButton = ttk.Button(master, text="Send", command=self.SendButtonClick)             
      self.sendButton.grid(column=1, padx=2, pady=6, row=2)

      self.statusText = ttk.Label(master, text="Using Photon, a Python IM client")
      self.statusText.grid(column=0, row=0, sticky=W)

      master.bind('<Return>', self.SendButtonClick) # Use return in addition to send button

      master.protocol("WM_DELETE_WINDOW", onProgramExit)
      
    except Exception:
      ReportError()

    
  def WriteLine(self, message):
    try:
      if message == "":
        return
      
      if message[-2:] != "\n":
         message += "\n"

      self.messageDisplay.config(state=NORMAL)
      self.messageDisplay.insert(END, message)
      self.messageDisplay.config(state=DISABLED)
      print(message[:-1])

    except Exception:
      ReportError()

  def SendButtonClick(self, optionalReturnHandler=None):
    SendMessage(self.messageInput.get(), self)

      
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
    
    
# Functions

def SendMessage(message, gui):
  try:
      global ServerSocket
      newMessagePacket = MessagePacket(gui.messageInput.get(), Username) # Create a new message packet
      ServerSocket.send(encode(newMessagePacket))
      gui.messageInput.delete(0, END)

  except Exception:
     ReportError()

def ReportError():
  traceback.print_exc()

# Dumps and Loads are not well named
def encode(packet):
  return pickle.dumps(packet)
def decode(packet):
  return pickle.loads(packet)

def formatUsername(name):
  return "<" + name + ">: "

def onProgramExit():
  global ServerSocket
  print("Window closed: Force closing all threads and server socket")
  ServerSocket.close()
  os._exit(1)


def ListenForPackets(server, gui):
  try:
    global ServerSocket
    while True:
      packet = decode(server.recv(1024))

      if packet.type == "PING":
        if packet.response == True:
          print("Pong")# will do more later
        elif packet.response == False: # Ping is not a response; the server wants a response
          newPingPacket = PingPacket(True)
          ServerSocket.send(encode(newPingPacket))

      elif packet.type == "MESSAGELIST":
        for element in packet.messageList:
          if element[0] == "SILENT":  gui.WriteLine(element[1])
          else: gui.WriteLine(formatUsername(element[0]) + element[1])
             
      elif packet.type == "MESSAGE":
        formatMessage(packet, gui)
        
  except Exception:
     ReportError()

def formatMessage(packet, gui):
  lineIndex = float(gui.messageDisplay.index('end')) - 1 # Get the line that the message will be on
  usernameLength = len(formatUsername(packet.sender))
  
  packet.message, italicRanges = formatBalsamiq(packet.message, "_")
  packet.message, boldRanges = formatBalsamiq(packet.message, "*")
  
  if packet.sender == "SILENT":  gui.WriteLine(packet.message) # Print the message
  else: gui.WriteLine(formatUsername(packet.sender) + packet.message)

  # Apply tags
  for italicRange in italicRanges: 
    italicStart = str(lineIndex)[:-2] + "." + str(italicRange[0] + usernameLength)
    italicEnd   = str(lineIndex)[:-2] + "." + str(italicRange[1] + usernameLength)
    gui.messageDisplay.tag_add("italic", italicStart, italicEnd)
    gui.messageDisplay.tag_config("italic", font=("Consolas", 10, "italic"))
  for boldRange in boldRanges: 
    boldStart = str(lineIndex)[:-2] + "." + str(boldRange[0] + usernameLength)
    boldEnd   = str(lineIndex)[:-2] + "." + str(boldRange[1] + usernameLength)
    gui.messageDisplay.tag_add("bold", boldStart, boldEnd)
    gui.messageDisplay.tag_config("bold", font=("Consolas", 10, "bold"))
    
  gui.master.update()
        

def formatBalsamiq(message, specialChar):
  try:
    global NONBREAKINGSPACE
    charCounter = 0
    charRanges = [] # Contains ranges of special char text sections

    charInstances = []
    i = 0
    while True: # Locate all instances of special char within message
      charInstance = message.find(specialChar, i)
      if charInstance == -1:
        break
      else:
        charInstances.append(charInstance)
        i = charInstance + 1

    print(charInstances)

    message = list(message) # Convert to list so we can substitute chars by index

    i = 0
    for charInstance in charInstances: # Ensure character is not escaped by '\'
      if message[charInstance - 1] == "\\":
        message[charInstance - 1] = NONPRINTINGCHAR
        del charInstances[i]
      else:
        i+= 1

    if len(charInstances) % 2 != 0: # Ignore special chars without a pair
      charInstances = charInstances[:-1]

    for i in range(0, len(charInstances), 2): # Subsitite special char for invisible char and determine start and end for formatted regions
      message[charInstances[i]] = NONPRINTINGCHAR
      message[charInstances[i + 1]] = NONPRINTINGCHAR
      charRanges.append((charInstances[i], charInstances[i+1]))

    message = "".join(message) # Convert back to string

    return message, charRanges
  except Exception:
     ReportError()


def __main__():
  global ServerSocket
  global Username
  atexit.register(onProgramExit)
  
  Username = input("Enter username: ")

  # Display UI
  root = Tk()
  gui = UserInterface(root)

  # Create a socket object
  ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

  # Get local machine name and assign a port
  host = socket.gethostname()
  port = 9999

  # Connect to hostname on the port.
  ServerSocket.connect((host, port))

  handshakePacket = ClientHandshakePacket(Username)
  ServerSocket.send(encode(handshakePacket))

  # Start listener thread for server responses
  listenerThread = Thread(target=ListenForPackets, args=(ServerSocket, gui))
  listenerThread.start()

  
  root.mainloop()
  #serverSocket.close()


if __name__ == "__main__":
   __main__()
