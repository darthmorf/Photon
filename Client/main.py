# Main Client File

import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5.uic import loadUi

import socket
import pickle                                    
from threading import Thread
import traceback
import atexit
import os
import re
import cgi
import time

# Load packet classes from shared libs
import sys
sys.path.insert(0, '../Libs')
from packets import *

# Global vars

MainGui = None
ServerSocket = None
Username = ""

NONPRINTINGCHAR = '\u200B' # Used to replace a character in a string whilst keeping indexes the same
MAXTRANSMISSIONSIZE = 4096

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

  def setUsername(self, username):
    self.usernameLabel.setText("Logged in as " + username)

  def closeEvent(self, event):
    # Not using onProgramExit() as it caused the program to hang when the UI is created
    global ServerSocket
    print("Window closed: Force closing all threads and server socket")
    ServerSocket.close()
    os._exit(1)

    
  def WriteLine(self, message):
    message = formatForDisplay(message)
    try:
      if message == "":
        return
      if message[-4:] != "<br>":
         message += "<br>"

      cursor = self.chatBox.textCursor()
      cursor.setPosition(len(self.chatBox.toPlainText()))
      self.chatBox.setTextCursor(cursor)
      self.chatBox.insertHtml(message)
      print(message[:-4])

    except Exception:
      ReportError()

  def onSendClick(self):
    text = self.messageInput.text()
    if not text.isspace() and text != "":
      SendMessage(text)
      self.messageInput.setText("")


class LoginWindow(QDialog):
  def __init__(self, *args):
    super(LoginWindow, self).__init__(*args)
    loadUi("login.ui", self)
    self.loginButton.clicked.connect(self.onLoginClick)
    self.usernameInput.returnPressed.connect(self.onLoginClick)

  def onLoginClick(self):
    global Username
    username = self.usernameInput.text()
    password = self.passwordInput.text()
    
    if not username.isspace() and username != "":

      if not password.isspace() and password != "":
        Password = password
        self.Login(username, password)
        
      else:
        self.errLabel.setText("Passwords must not consist of whitespace only")
      
    else:
      self.errLabel.setText("Usernames must not consist of whitespace only")

  def Login(self, username, password):
    global ServerSocket
    global Username
    loginRequest = LoginRequestPacket(username, password)
    ServerSocket.send(encode(loginRequest))

    loginResponsePacket = decode(ServerSocket.recv(MAXTRANSMISSIONSIZE))
    if loginResponsePacket.valid:
      self.close()
      Username = username
      
    else:
      self.errLabel.setText("Incorrect username or password")
       
    
# Functions

def SendMessage(message):
  try:
      global ServerSocket
      global Username
      newMessagePacket = MessagePacket(message, Username) # Create a new message packet
      ServerSocket.send(encode(newMessagePacket))

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
  os._exit(1)


def ListenForPackets(server):
  try:
    global ServerSocket
    global MainGui
  
    readyToListen = ReadyToListenPacket()
    ServerSocket.send(encode(readyToListen))
    
    while True:
      packet = decode(server.recv(MAXTRANSMISSIONSIZE))

      if packet.type == "MESSAGELIST":
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
  if packet.sender == "SILENT":  MainGui.WriteLine(packet.message) # Print the message
  else: MainGui.WriteLine(formatUsername(packet.sender) + packet.message)
        

def formatForDisplay(message):
  try:
    message = cgi.escape(message) # Escape html code; sanitise input
    # Replace balsamiq chars in pairs with html
    message = formatBalsmaiq(message, "*", "b")
    message = formatBalsmaiq(message, "_", "i")
    message = formatBalsmaiq(message, "~", "s")
    message = formatBalsmaiq(message, "!", "u")

    return message
  except Exception:
     ReportError()

def formatBalsmaiq(message, specialChar, tag):
  global NONPRINTINGCHAR
  charInstances = []
  i = 0
  while True: # Locate all instances of special char within message
    charInstance = message.find(specialChar, i)
    if charInstance == -1:
      break
    else:
      charInstances.append(charInstance)
      i = charInstance + 1
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

  for i in range(0, len(charInstances), 2): # Replace pairs of balsamiq with html code
    message[charInstances[i]] = "<" + tag + ">"
    message[charInstances[i + 1]] = "</" + tag + ">"

  message = "".join(message) # Convert back to string
  return message

def __main__():
  global ServerSocket
  global MainGui
  global Username
  global Password
  atexit.register(onProgramExit)

  # Print PyQt 'silent' errors 
  sys._excepthook = sys.excepthook 
  def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1) 
  sys.excepthook = exception_hook

  # Create a socket object
  ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

  # Get local machine name and assign a port
  host = socket.gethostname()
  port = 9998

  # Connect to hostname on the port.
  ServerSocket.connect((host, port))

  # Display UI
  app = QApplication(sys.argv)
  MainGui = MainWindow()
  loginGui = LoginWindow()
  loginGui.exec_()
  if Username == "": # Window was closed without an input
    os._exit(1)
  MainGui.setUsername(Username)
  MainGui.show()
  
  # Start listener thread for server responses
  listenerThread = Thread(target=ListenForPackets, args=(ServerSocket,))
  listenerThread.start()
    
  sys.exit(app.exec_())


if __name__ == "__main__":
   __main__()
