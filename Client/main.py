# Main Client File

from tkinter import *
import socket
import pickle                                    
from threading import Thread

# Global vars

ServerSocket = None
Username = ""

# Classes

class UserInterface:
  def __init__(self, master):
    self.master = master
    master.title("Photon - IM Client")
    master.iconbitmap(r".\icon.ico")

    master.geometry('1032x516') #Create a new window with resolution 1280x720 (scalable)
    master.resizable(False, False)
    
    self.messageDisplay = Text(master, height=28, width=128, relief="groove", state="disabled")
    self.messageDisplay.grid(column=0, columnspan=2, padx=2, pady=2, row=1) #Set the messageDisplay to expand dynamically

    self.messageInput = Entry(master, justify="left", relief="groove", takefocus="true", width=160)
    self.messageInput.grid(column=0, padx=2, pady=6, row=2)

    self.sendButton = Button(master, text="Send", command=self.SendButtonClick)             
    self.sendButton.grid(column=1, padx=2, pady=6, row=2)

    self.statusText = Label(master, text="Using Photon, a Python IM client")
    self.statusText.grid(column=0, row=0, sticky=W)

    
  def WriteLine(self, message):
    if message == "":
      return
    
    if message[-2:] != "\n":
       message += "\n"

    self.messageDisplay.config(state=NORMAL)
    self.messageDisplay.insert(END, message)
    self.messageDisplay.config(state=DISABLED)
    print("Displayed message:", message)

  def SendButtonClick(self):
    global ServerSocket
    ServerSocket.send(encode(Username + ": " + self.messageInput.get()))
    self.messageInput.delete(0, END)


# Functions

# Dumps and Loads are not well named
def encode(packet):
  return pickle.dumps(packet)
def decode(packet):
  return pickle.loads(packet)


def ListenForPackets(server, gui):
  while True:
    message = decode(server.recv(1024))
    gui.WriteLine(message)


def __main__():
  global ServerSocket
  global Username
  Username = "<" + input("Enter username: ") + ">"

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
