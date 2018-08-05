# Main Client File

import sys
import socket
import pickle                                    
from threading import Thread
import traceback
import atexit
import os
import re
import cgi
import time
import urllib.request
import re

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5.uic import loadUi

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
    try:
      self.usernameLabel.setText("Logged in as " + username)
    except Exception:
      ReportError()


  def closeEvent(self, event):
    try:
      # Not using onProgramExit() as it caused the program to hang when the UI is created
      global ServerSocket
      print("Window closed: Force closing all threads and server socket")
      ServerSocket.close()
      os._exit(1)
    except Exception:
      ReportError()

 
  def WriteLine(self, message):
    message = formatForDisplay(message)
    try:
      if message == "":
        return
      if message[-4:] != "<br>":
         message += "<br>"

      url = re.search("(?P<url>https?://[^\s]+)", message)
      if url is not None:
        url = url.group("url")[:-4]

        if "png" in url[-3:] or "jpg" in url[-3:]:
          print("url:   ", url)
          file = downloadImage(url)

          message += "<img src='" + file + "' height='50' width='50'/><br>"

      cursor = self.chatBox.textCursor()
      cursor.setPosition(len(self.chatBox.toPlainText()))
      self.chatBox.setTextCursor(cursor)
      self.chatBox.insertHtml(message)
      print(message[:-4])
    except Exception:
      ReportError()


  def onSendClick(self):
    try:
      text = self.messageInput.text()
      if not text.isspace() and text != "":
        SendMessage(text)
        self.messageInput.setText("")
    except Exception:
      ReportError()


class LoginWindow(QDialog):
  def __init__(self, *args):
    try:
      super(LoginWindow, self).__init__(*args)
      loadUi("login.ui", self)
      self.loginButton.clicked.connect(self.onLoginClick)
      self.newAccButton.clicked.connect(self.openRegisterWindow)
      self.usernameInput.returnPressed.connect(self.onLoginClick)
    except Exception:
      ReportError()


  def openRegisterWindow(self):
    try:
      registerGui = RegisterWindow()
      registerGui.exec_()
    except Exception:
      ReportError()


  def onLoginClick(self):
    try:
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
    except Exception:
      ReportError()


  def Login(self, username, password):
    try:
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
    except Exception:
      ReportError()


class RegisterWindow(QDialog):
  def __init__(self, *args):
    try:
      super(RegisterWindow, self).__init__(*args)
      loadUi("register.ui", self)
      self.registerButton.clicked.connect(self.validateInputs)
    except Exception:
      ReportError()

  def validateInputs(self):
    try:
      username = self.usernameInput.text()
      password1 = self.passwordInput1.text()
      password2 = self.passwordInput2.text()

      if not username.isspace() and username != "":
        if password1 == password2:
          if not password1.isspace() and password1 != "":
            self.register(username, password1)
          else:
            self.errLabel.setText("Passwords must not consist of whitespace only")
        else:
          self.errLabel.setText("Passwords must match")
      else:
        self.errLabel.setText("Usernames must not consist of whitespace only")
    except Exception:
      ReportError()

  def register(self, username, password):
    try:
      registerPacket = RegisterPacket(username, password)
      global ServerSocket
      ServerSocket.send(encode(registerPacket))
      userCreatePacket = decode(ServerSocket.recv(MAXTRANSMISSIONSIZE)) # Wait for user to be created
      self.close()
    except Exception:
      ReportError()



    
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


# Dumps and Loads are badly named
def encode(packet):
  return pickle.dumps(packet)
def decode(packet):
  return pickle.loads(packet)


def formatUsername(name):
  return "[" + name + "]: "


def onProgramExit():
  try:
    global ServerSocket
    print("Window closed: Force closing all threads and server socket")
    ServerSocket.close()
    os._exit(1)
  except Exception:
      ReportError()


def ListenForPackets(server):
  try:
    global ServerSocket
    global MainGui
  
    readyToListen = Packet("READYTOLISTEN") # Tell the server we are ready to listen using generic packet
    ServerSocket.send(encode(readyToListen))
    
    while True:
      packet = decode(server.recv(MAXTRANSMISSIONSIZE))

      if packet.type == "MESSAGELIST":
        for element in packet.messageList:
          if element[0] == "SERVER":
            MainGui.WriteLine(element[1])
          else: MainGui.WriteLine(formatUsername(element[0]) + element[1])
             
      elif packet.type == "MESSAGE":
        formatMessage(packet)
        
  except Exception:
     ReportError()


def formatMessage(packet):
  try:
    global MainGui
    if packet.sender == "SERVER":  MainGui.WriteLine(packet.message) # Print the message
    else: MainGui.WriteLine(formatUsername(packet.sender) + packet.message)
  except Exception:
      ReportError()
        

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
  try:
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
  except Exception:
      ReportError()

def downloadImage(url):
  filename = "cachedimgs/" + time.strftime("%Y-%m-%d %H:%M:%S").replace(":","").replace("-","").replace(" ","") + ".jpg"
  urllib.request.urlretrieve(url, filename)
  return filename


def __main__():
  try:
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
  except Exception:
      ReportError()


if __name__ == "__main__":
   __main__()
