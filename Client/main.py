# Main Client File

import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

import socket
import pickle                                    
from threading import Thread
import traceback
import atexit
import os
import re
import cgi

# Global vars

MainGui = None
ServerSocket = None
Username = ""

NONPRINTINGCHAR = '\u200B' # Used to replace a character in a string whilst keeping indexes the same

# Classes

class MainWindow(QMainWindow):
  def __init__(self, *args):
    try:
      super(MainWindow, self).__init__(*args)
      loadUi("mainWindow.ui", self)
      self.messageInputButton.clicked.connect(self.onSendClick)
      self.messageInput.returnPressed.connect(self.onSendClick)
      
    except Exception:
      ReportError()

    
  def WriteLine(self, message):
    message = formatForDisplay(message)
    try:
      if message == "":
        return
      if message[-2:] != "<br>":
         message += "<br>"
      self.chatBox.insertHtml(message)
      print(message[:-1])

    except Exception:
      ReportError()

  def onSendClick(self):
    SendMessage(self.messageInput.text())
    self.messageInput.setText("")


      
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

def SendMessage(message):
  try:
      global ServerSocket
      global Username
      newMessagePacket = MessagePacket(message, Username) # Create a new message packet
      ServerSocket.send(encode(newMessagePacket))
      #gui.messageInput.delete(0, END)

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
  return "[" + name + "]: "

def onProgramExit():
  global ServerSocket
  print("Window closed: Force closing all threads and server socket")
  ServerSocket.close()
  sys.exit(app.exec_())
  os._exit(1)


def ListenForPackets(server):
  try:
    global ServerSocket
    global MainGui
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
          if element[0] == "SILENT":
            MainGui.WriteLine(element[1])
          else: MainGui.WriteLine(formatUsername(element[0]) + element[1])
             
      elif packet.type == "MESSAGE":
        formatMessage(packet)
        
  except Exception:
     ReportError()

def formatMessage(packet):
  global MainGui
  if packet.sender == "SILENT":  gui.WriteLine(packet.message) # Print the message
  else: MainGui.WriteLine(formatUsername(packet.sender) + packet.message)
        

def formatForDisplay(message):
  try:
    global NONBREAKINGSPACE
    message = cgi.escape(message) # Escape html
    # replace balsamiq chars in pairs with html

    return message
  except Exception:
     ReportError()

def __main__():
  global ServerSocket
  global Username
  global MainGui
  atexit.register(onProgramExit)

  # Print PyQt 'silent' errors 
  sys._excepthook = sys.excepthook 
  def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1) 
  sys.excepthook = exception_hook 
  
  Username = input("Enter username: ")

  # Display UI
  app = QApplication(sys.argv)
  MainGui = MainWindow()
  MainGui.show()

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
  listenerThread = Thread(target=ListenForPackets, args=(ServerSocket,))
  listenerThread.start()
    
  sys.exit(app.exec_())
  #serverSocket.close()


if __name__ == "__main__":
   __main__()
