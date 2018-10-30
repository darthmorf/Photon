# Main Client File

import sys
import socket
import pickle                                    
from threading import Thread
import atexit
import os
import cgi
import time
import datetime

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QWidget, QFormLayout, QScrollArea
from PyQt5.uic import loadUi

# Load classes and functions from shared libs
import sys
sys.path.insert(0, '../Libs')
from packets import *
from photonUtilities import *



# Global vars
Debug = False

App = None
MainGui = None
ServerSocket = None
Username = ""
UserId = None
Admin = False

NONPRINTINGCHAR = '\u200B' # Used to replace a character in a string whilst keeping indexes the same
MAXTRANSMISSIONSIZE = 40960
COMMANDCHAR = "/"


# Classes

class MainWindow(QMainWindow):

  # Signals for updating the GUI
  writeSignal = pyqtSignal(Message)
  usersChangedSignal = pyqtSignal(list)

  def __init__(self, *args):
    try:
      super(MainWindow, self).__init__(*args)
      loadUi("mainWindow.ui", self)
      self.messageInputButton.clicked.connect(self.onSendClick)
      self.messageInput.returnPressed.connect(self.onSendClick)
      # Point the signals to the corresponding functions
      self.writeSignal.connect(self.WriteLine) 
      self.usersChangedSignal.connect(self.UpdateConnectedUsers)
      self.messageWidget.setLayout(self.messageLayout)        
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
      debugPrint("Window closed: Force closing all threads and server socket", Debug)
      ServerSocket.close()
      os._exit(1)
    except Exception:
      ReportError()


  def WriteLine(self, message):
    rawMessage = message.contents
    message.contents = formatTextForDisplay(message.contents, message.colour)
    #message.timeSent = formatDateTime(message.timeSent)
    message.senderName = formatUsername(message.senderName)
    rawMessage = message
    try:
      newWidget = MessageWidget() # Create a new message widget
      newWidget.timeLabel.setText(message.timeSent)
      newWidget.usernameLabel.setText(message.senderName)
      newWidget.messageLabel.setText(message.contents)
      rowCount = self.messageLayout.rowCount() # Get the amount of rows in the message container
      self.messageLayout.setWidget(rowCount, QFormLayout.LabelRole, newWidget) # Append the new message widget to the end of the container   

      debugPrint(rawMessage, Debug)
      App.alert(MainGui, 1000) # Flash the taskbar icon for 1 second
    except Exception:
      ReportError()

    
  def UpdateConnectedUsers(self, userList):
    userCount = len(userList)
    self.userCountLabel.setText("Users Online: " + str(userCount))
    
    self.userListBox.clear()
    for user in userList:
      self.userListBox.insertHtml(user + "<br>")


  def onSendClick(self):
    try:
      text = self.messageInput.text()
      if not text.isspace() and text != "":
        if text[0] == COMMANDCHAR:
          ParseCommand(text)
        else:
          SendMessage(text)
        self.messageInput.setText("")
    except Exception:
      ReportError()


class MessageWidget(QWidget):
  def __init__(self, parent=None):
      super(MessageWidget, self).__init__(parent)
      loadUi("message.ui", self)


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
      global ServerSocket, Username, UserId
      password = HashString(password)
      loginRequest = LoginRequestPacket(username, password)
      ServerSocket.send(encode(loginRequest))

      loginResponsePacket = decode(ServerSocket.recv(MAXTRANSMISSIONSIZE))

      if loginResponsePacket.type != "LOGINRESPONSE":
        self.Login(username, password) # Occasionally a left-over packet can make it's way here - if so we'll just try again
        return

      if loginResponsePacket.valid:
        self.close()
        Username = username
        UserId = loginResponsePacket.id
        Admin = loginResponsePacket.admin
        
      else:
        self.errLabel.setText(loginResponsePacket.err)
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

      if not username.isspace() and username != "" and len(username) < 33:
        if password1 == password2:
          if not password1.isspace() and password1 != "":
            self.register(username, password1)
          else:
            self.errLabel.setText("Passwords must not consist of whitespace only")
        else:
          self.errLabel.setText("Passwords must match")
      else:
        self.errLabel.setText("Usernames must not consist of whitespace only, and be\nless than 33 chars long")
    except Exception:
      ReportError()

  def register(self, username, password):
    try:
      password = HashString(password)
      registerPacket = RegisterPacket(username, password)
      global ServerSocket
      ServerSocket.send(encode(registerPacket))
      registerResponse = decode(ServerSocket.recv(MAXTRANSMISSIONSIZE)) # Wait for user creation packet response
      if registerResponse.valid:
        successNotifier = QMessageBox()
        successNotifier.setIcon(QMessageBox.Information)
        successNotifier.setText("Successfully registered user '" + username + "'")
        successNotifier.setWindowTitle("Account creation successful")
        successNotifier.exec_()
        self.close()
      else:
        self.errLabel.setText(registerResponse.err)
    except Exception:
      ReportError()



    
# Functions

def SendMessage(message):
  try:
      global ServerSocket, Username
      debugPrint(UserId, Debug)
      newMessage = Message(UserId, Username, message)
      newMessagePacket = MessagePacket(newMessage)
      ServerSocket.send(encode(newMessagePacket))

  except Exception:
     ReportError()


def ParseCommand(command):
  try:
    global ServerSocket
    command = command[1:] # Strip command char
    args = command.split(" ") 
    command = args[0]
    del args[0]
    commandPacket = CommandPacket(command, args)
    ServerSocket.send(encode(commandPacket))
    
  except Exception:
    ReportError()
    

def printMessage(message):
  if type(message) is str:
    message = Message(contents=message)

  MainGui.writeSignal.emit(message)


def onProgramExit():
  try:
    global ServerSocket
    debugPrint("Window closed: Force closing all threads and server socket", Debug)
    ServerSocket.close()
    os._exit(1)
  except Exception:
      ReportError()


def ListenForPackets(server):
  try:
    global ServerSocket, MainGui
  
    readyToListen = Packet("READYTOLISTEN") # Tell the server we are ready to listen using generic packet
    ServerSocket.send(encode(readyToListen))
    
    while True:
      packet = decode(server.recv(MAXTRANSMISSIONSIZE))

      if packet.type == "MESSAGELIST":
        for message in packet.messageList:
          printMessage(message)
             
      elif packet.type == "MESSAGE":
        formatMessage(packet)

      elif packet.type == "USERLIST":
        MainGui.usersChangedSignal.emit(packet.userList)

      elif packet.type == "COMMANDRESPONSE":
        if packet.success:
          if packet.command == "help":
            printMessage(packet.response[0])
            for i in range(1, len(packet.response)):
              printMessage(" - *" + packet.response[i][0] + "* : " + packet.response[i][1])

          if packet.command == "markup":
            printMessage(packet.response[0])
            printMessage(packet.response[1])
            for i in range(2, len(packet.response)):
              printMessage(" - " + packet.response[i][0] + ", " + packet.response[i][1] + " : " + packet.response[i][2])
          
          elif packet.command == "ping":
            printMessage(Message(contents=packet.response, colour=INFO))

          elif packet.command == "whisper":
            printMessage(Message(contents=formatDateTime(packet.timeSent) + packet.response, colour=INFO))
            
        else:
          printMessage(Message(contents="Error executing command '" + packet.command + "' - " + packet.err, colour=COMMANDERROR))
          
          

  except Exception:
    ReportError() 


def formatMessage(packet):
  try:
    printMessage(packet.message)
  except Exception:
      ReportError()
        

def formatTextForDisplay(message, colour):
  try:
    message = cgi.escape(message) # Escape html code; sanitise input
    # Replace balsamiq chars in pairs with html
    message = formatBalsmaiq(message, "*", "b")
    message = formatBalsmaiq(message, "_", "i")
    message = formatBalsmaiq(message, "~", "s")
    message = formatBalsmaiq(message, "!", "u")

    message = "<font color='" + colour + "'>" + message + "</font>"

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


def __main__():
  try:
    global ServerSocket, Username, Password
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
    global GuiDone, App, MainGui
    App = QApplication(sys.argv)
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

    sys.exit(App.exec_())
      
  except Exception:
      ReportError()


if __name__ == "__main__":
   __main__()
