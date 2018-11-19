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
import re

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QWidget, QFormLayout, QScrollArea, QTableWidgetItem
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
  """
  GUI Class for main window. Inherits QMainWindow.

  Elements:
    centralWidget (QWidget): Main area containg window elements.
    adminSettinsButton (QPushButton): Button to open admin settings.
    messageInput (QLineEdit): Input area for sending messages.
    messageInputButton (QPushButton): Send button for messages.
    messageScrollArea (QScrollArea): Window section containing message elements.
    messageWidget (QWidget): Widget to contain message elements.
    userCountLabel (QLabel): Displays count of online users.
    userListBox (QTextEdit): Contains all online users.
    usernameLabel (QLabel): Displays username.

  Properties:
    writeSignal (QSignal): Signal to trigger message creation.
    usersChangedSignal (QSignal): Signal to update online users.

  ToDo:
    Seperate this class out!
  """

  # Signals for updating the GUI
  writeSignal = pyqtSignal(Message)
  usersChangedSignal = pyqtSignal(list)
  updateMessageSignal = pyqtSignal(int, str)
  deleteMessageSignal = pyqtSignal(int)

  def __init__(self, *args):
    """ Initialises the UI and connects all signals and button clicks. """
    try:
      super().__init__(*args)
      loadUi("mainWindow.ui", self)
      self.messageInputButton.clicked.connect(self.onSendClick)
      self.messageInput.returnPressed.connect(self.onSendClick)
      # Point the signals to the corresponding functions
      self.writeSignal.connect(self.WriteLine) 
      self.usersChangedSignal.connect(self.UpdateConnectedUsers)
      self.updateMessageSignal.connect(self.updateMessageContents)
      self.deleteMessageSignal.connect(self.deleteMessage)
      self.messageWidget.setLayout(self.messageLayout)
        
    except Exception:
      ReportError()


  def setUsername(self, username):
    """
    Sets the username label text.

    Args:
      username (string): The username to set to.
    """
    try:
      self.usernameLabel.setText(f"Logged in as {username}")
    except Exception:
      ReportError()


  def postLogin(self):
    """ Setup for after login is completed. """
    if not Admin:
        self.adminSettingsButton.hide()
    else:
        self.adminSettingsButton.clicked.connect(self.openAdminSettings)
        
  def openAdminSettings(self):
    """ Opens the admin settings UI. """
    try:
      self.adminSettings = AdminSettingsWindow(self)
      self.adminSettings.show()
    except Exception:
      ReportError()
  

  def closeEvent(self, event):
    """ When main window closed, tidy up loose ends and exit. """
    try:
      # Not using onProgramExit() as it caused the program to hang when the UI is created
      global ServerSocket
      debugPrint("Window closed: Force closing all threads and server socket", Debug)
      ServerSocket.close()
      os._exit(1)
    except Exception:
      ReportError()


  def WriteLine(self, message):
    """
    Formats message, creates a new element for it and displays it properly.

    Args:
      message (Message): The message to display
    """
    rawMessage = message.contents
    try:
      newWidget = MessageWidget(message=message) # Create a new message widget
      newWidget.updateText()
      rowCount = self.messageLayout.rowCount() # Get the amount of rows in the message container
      self.messageLayout.setWidget(rowCount, QFormLayout.LabelRole, newWidget) # Append the new message widget to the end of the container   
      newWidget.setFixedWidth(self.messageScrollArea.width() - 10) # Set widget width to match the parent width

      debugPrint(rawMessage, Debug)
      App.alert(MainGui, 1000) # Flash the taskbar icon for 1 second
    except Exception:
      ReportError()

    
  def UpdateConnectedUsers(self, userList):
    """
    Update connected users GUI elements.

    Args:
      userList (list of string): List of online users.
    """
    userCount = len(userList)
    self.userCountLabel.setText(f"Users Online: {userCount}")
    
    self.userListBox.clear()
    for user in userList:
      self.userListBox.insertHtml(f"{user} <br>")


  def onSendClick(self):
    """ When the send button is pressed, take input, parse it and then send it. """
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


  def resizeEvent(self, event): 
    """ Overrides the window resize event. Updates widget sizes. """
    width = self.messageScrollArea.width() - 10
    messageWidgets = (self.messageLayout.itemAt(i) for i in range(self.messageLayout.count())) # Get a list of widgets in layout

    for layoutItem in messageWidgets:
      layoutItem.widget().setFixedWidth(width)


  def updateMessageContents(self, messageId, contents):
    messageWidgets = (self.messageLayout.itemAt(i) for i in range(self.messageLayout.count())) # Get a list of widgets in layout
    
    for layoutItem in messageWidgets:
      if layoutItem.widget().message.messageId == messageId:
        layoutItem.widget().message.contents = contents
        layoutItem.widget().updateText()

  def deleteMessage(self, messageId):
    messageWidgets = (self.messageLayout.itemAt(i) for i in range(self.messageLayout.count())) # Get a list of widgets in layout
    
    for layoutItem in messageWidgets:
      if layoutItem.widget().message.messageId == messageId:
        layoutItem.widget().message.contents = "_message deleted_"
        layoutItem.widget().message.senderId = 1
        layoutItem.widget().message.senderName = "SERVER"
        layoutItem.widget().message.colour = INFO
        layoutItem.widget().updateText()



class MessageWidget(QWidget):
  """ Gui Class for each message. """
  def __init__(self, parent=None, message=""):
      super().__init__(parent)
      loadUi("message.ui", self)
      self.messageOptionBtn.clicked.connect(lambda: self.openMessageOptions())
      self.message = message

  def openMessageOptions(self):
    """ Opens UI for managing messages. """
    try:
      self.messageOptions = MessageOptions(self, message=self.message)
      self.messageOptions.show()
    except Exception:
      ReportError()

  def updateText(self):
      self.timeLabel.setText(self.message.timeSent)
      self.usernameLabel.setText(formatUsername(self.message.senderName))
      self.messageLabel.setText(formatTextForDisplay(self.message.contents, self.message.colour))

class MessageOptions(QDialog):
  """ 
  GUI Class for managing messages

  Args:
    timestamp (string): Time that the message was sent.
    user (string): Username of user who sent the message.
    message (string): The contents of the message being managed.
  """
  def __init__(self, *args, message=""):
    try:
      super().__init__(*args)
      loadUi("messageOptions.ui", self)
      self.reportButton.clicked.connect(lambda: self.sendReport())
      self.editButton.clicked.connect(lambda: self.editMessageContents())
      self.deleteButton.clicked.connect(lambda: self.deleteMessage())
      self.message = message
      self.timeLabel.setText(message.timeSent)
      self.usernameLabel.setText(formatUsername(message.senderName))
      self.editMessage.setText(message.contents)

      # Users can only edit and delete their own messages. Admins can delete any message. You cannot report your own or a server message. Local messages cannot be modified.
      if self.message.senderId != UserId or self.message.senderId == "":
        self.editMessage.setEnabled(False)
        self.editButton.setEnabled(False)
        if not Admin or self.message.senderId == "":
          self.deleteButton.setEnabled(False)
      
      if self.message.senderId == 1 or self.message.senderId == UserId or self.message.senderId == "":
        self.reportButton.setEnabled(False)
        self.reportReason.setEnabled(False)

    except Exception:
      ReportError()

  def sendReport(self):
    reason = self.reportReason.text()
    if len(reason) < 1:
      errNotifier = QMessageBox()
      errNotifier.setIcon(QMessageBox.Critical)
      errNotifier.setText("You must supply a reason when reporting a message.")
      errNotifier.setWindowTitle("Report Error")
      errNotifier.exec_()
    else:
      reportPacket = ReportPacket(self.message.messageId, UserId, reason)
      ServerSocket.send(encode(reportPacket))
      successNotifier = QMessageBox()
      successNotifier.setIcon(QMessageBox.Information)
      successNotifier.setText("Successfully reported message.")
      successNotifier.setWindowTitle("Report Result")
      successNotifier.exec_()

  def editMessageContents(self):
    editMessagePacket = EditMessagePacket(self.message.messageId, self.editMessage.text())
    ServerSocket.send(encode(editMessagePacket))
    successNotifier = QMessageBox()
    successNotifier.setIcon(QMessageBox.Information)
    successNotifier.setText("Successfully edited message.")
    successNotifier.setWindowTitle("Edit Result")
    successNotifier.exec_()

  def deleteMessage(self):
    deleteMessagePacket = DeleteMessagePacket(self.message.messageId)
    ServerSocket.send(encode(deleteMessagePacket))
    successNotifier = QMessageBox()
    successNotifier.setIcon(QMessageBox.Information)
    successNotifier.setText("Successfully deleted message.")
    successNotifier.setWindowTitle("Delete Result")
    successNotifier.exec_()
    self.close()


class AdminSettingsWindow(QDialog):      
  """ GUI Class for the admin window. """
  def __init__(self, *args):
      super().__init__(*args)
      loadUi("adminSettings.ui", self)
      self.userListComboBox.currentIndexChanged.connect(self.ComboBoxUpdated)
      requestUserListPacket = Packet("REQUESTUSERLIST")
      ServerSocket.send(encode(requestUserListPacket))

  def UserListReceived(self, userList):
    """ 
    Populates the userList dropdown.

    Args:
      userList (list of string): The list of users. 
    """
    for user in userList:
      self.userListComboBox.addItem(user[1])

  def ComboBoxUpdated(self):
    """ Event for when a new user is selected from the combobox. Fetches information about that user. """
    requestUserInfoPacket = RequestUserInfoPacket(self.userListComboBox.currentText())
    ServerSocket.send(encode(requestUserInfoPacket))

  def UpdateUserInfo(self, userId, messageCount, flags):
    """
    Updates the user specific info sections.

    Args:
      userId (int): The id of the selected user.
      messageCount (int): The amount of messages sent by that user.
      flags  (list of (string, string, string, int)): The report details of that user. Corresponding to list of (reported message, report reason, reporter name, reporter id)
    """
    self.userIdLabel.setText(str(userId))
    self.messageCountLabel.setText(str(messageCount))
    self.reportCountLabel.setText(str(len(flags)))
    
    rowPosition = self.reportTable.rowCount()
    for row in range(0, rowPosition):
      self.reportTable.removeRow(1)

    i = 1
    for flag in flags:
      self.reportTable.insertRow(i)
      self.reportTable.setItem(i, 0, QTableWidgetItem(str(flag[0])))
      self.reportTable.setItem(i, 1, QTableWidgetItem(str(flag[1])))
      self.reportTable.setItem(i, 2, QTableWidgetItem(f"{flag[2]} (ID: {flag[3]})"))
      i += 1


class LoginWindow(QDialog):
  """ GUI Class for login window """
  def __init__(self, *args):
    try:
      super().__init__(*args)
      loadUi("login.ui", self)
      self.loginButton.clicked.connect(self.onLoginClick)
      self.newAccButton.clicked.connect(self.openRegisterWindow)
      self.usernameInput.returnPressed.connect(self.onLoginClick)
    except Exception:
      ReportError()


  def openRegisterWindow(self):
    """ Opens register window GUI """
    try:
      registerGui = RegisterWindow()
      registerGui.exec_()
    except Exception:
      ReportError()


  def onLoginClick(self):
    """ Called on login button click. Basic input validation. """
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
    """
    Attempts to login user to server.

    Args:
      username (string): Username to login with.
      password (string): Password to login with, not yet hashed.
    """
    try:
      global ServerSocket, Username, UserId, Admin
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
  """ GUI Class for register window """
  def __init__(self, *args):
    try:
      super().__init__(*args)
      loadUi("register.ui", self)
      self.registerButton.clicked.connect(self.validateInputs)
    except Exception:
      ReportError()

  def validateInputs(self):
    """ Called on register button click. Basic input validation. """
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
    """
    Attempts to register user with server.
    
    Args:
      username (string): Username to register.
      password (string): Password to register, not yet hashed.
    """
    try:
      password = HashString(password)
      registerPacket = RegisterPacket(username, password)
      global ServerSocket
      ServerSocket.send(encode(registerPacket))
      registerResponse = decode(ServerSocket.recv(MAXTRANSMISSIONSIZE)) # Wait for user creation packet response
      if registerResponse.valid:
        successNotifier = QMessageBox()
        successNotifier.setIcon(QMessageBox.Information)
        successNotifier.setText(f"Successfully registered user '{username}'")
        successNotifier.setWindowTitle("Account creation successful")
        successNotifier.exec_()
        self.close()
      else:
        self.errLabel.setText(registerResponse.err)
    except Exception:
      ReportError()



    
# Functions
"""
Constructs a message object and sends it to the server.

Args:
  message (string): The message contents.
"""
def SendMessage(message):
  try:
      global ServerSocket, Username
      debugPrint(UserId, Debug)
      newMessage = Message(UserId, Username, message)
      newMessagePacket = MessagePacket(newMessage)
      ServerSocket.send(encode(newMessagePacket))

  except Exception:
     ReportError()

"""
Formats a command string into arguments and sends it to the server.

Args:
  command (string): The raw command text before formatting.
"""
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
    
"""
Ensures a message is in the correct format and then passes it to the GUI to display.

Args:
  message (string, optional): The string to convert to message object.
  message (Message, optional): The message object to pass to the GUI.
"""
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

      elif packet.type == "ONLINEUSERS":
        MainGui.usersChangedSignal.emit(packet.userList)

      elif packet.type == "COMMANDRESPONSE":
        if packet.success:
          if packet.command == "help":
            printMessage(packet.response[0])
            for i in range(1, len(packet.response)):
              printMessage(f" - *{packet.response[i][0]}* : {packet.response[i][1]}")

          if packet.command == "markup":
            printMessage(packet.response[0])
            printMessage(packet.response[1])
            for i in range(2, len(packet.response)):
              printMessage(f" - {packet.response[i][0]}, {packet.response[i][1]} : {packet.response[i][2]}")
          
          elif packet.command == "ping":
            printMessage(Message(contents=packet.response, colour=INFO))

          elif packet.command == "whisper":
            printMessage(Message(contents=formatDateTime(packet.timeSent) + packet.response, colour=INFO))
            
        else:
          printMessage(Message(contents=f"Error executing command '{packet.command}' - {packet.err}", colour=COMMANDERROR))


      elif packet.type == "USERLIST":
        MainGui.adminSettings.UserListReceived(packet.userList)


      elif packet.type == "USERINFO":
        MainGui.adminSettings.UpdateUserInfo(packet.id, packet.messageCount, packet.flags)

      elif packet.type == "EDITMESSAGE":
        MainGui.updateMessageSignal.emit(packet.messageId, packet.newContents)

      elif packet.type == "DELETEMESSAGE":
        MainGui.deleteMessageSignal.emit(packet.messageId)

      else:
          print(f"Unknown packet received: {packet.type}")
          
          

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

    message = f"<font color='{colour}'> {message} </font>"

    return message
  except Exception:
     ReportError()

def inverseFormatTextForDisplay(message):
    try:
      colour = re.search("<font color='(.+?)'>", message).group(1) # Use regex to extract the hex colour code of the message
      # Replace html pairs with balsamiq
      message = re.sub("<b>|</b>", "*", message)
      message = re.sub("<i>|</i>", "_", message)
      message = re.sub("<s>|</s>", "~", message)
      message = re.sub("<u>|</u>", "!", message)
      message = re.sub('<[^<]+?>', '', message) # strip remaining html code

      return (message, colour)
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
      message[charInstances[i]] = f"<{tag}>"
      message[charInstances[i + 1]] = f"</{tag}>"

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
    MainGui.postLogin()
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
