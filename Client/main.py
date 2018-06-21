# Main Client File

from tkinter import *
from tkinter import ttk
import socket
import pickle                                    
from threading import Thread
import traceback
import atexit
import os

# Global vars

ServerSocket = None
Username = ""

# Classes

class UserInterface:
  def __init__(self, master):
    try:
      self.master = master
      master.title("Photon - IM Client")
      master.iconbitmap(r".\icon.ico")

      master.geometry('1032x516') #Create a new window with resolution 1280x720 (scalable)
      master.resizable(False, False)
      
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
        gui.WriteLine(formatUsername(element[0]) + element[1])
           
    elif packet.type == "MESSAGE":
      gui.WriteLine(formatUsername(packet.sender) + packet.message)


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

  # Start listener thread for server responses
  listenerThread = Thread(target=ListenForPackets, args=(ServerSocket, gui))
  listenerThread.start()

  
  root.mainloop()
  #serverSocket.close()


if __name__ == "__main__":
   __main__()
