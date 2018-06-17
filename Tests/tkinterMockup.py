from tkinter import *

class UserInterface:
  def __init__(self, master):
    self.master = master
    master.title("Photon - IM Client")

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
    
    message = "<User>: " + str(message)
    if message[-2:] != "\n":
       message += "\n"

    self.messageDisplay.config(state=NORMAL)
    self.messageDisplay.insert(END, message)
    self.messageDisplay.config(state=DISABLED)
    print("Displayed message:", message[-2:])

  def SendButtonClick(self):
    self.WriteLine(self.messageInput.get())
    self.messageInput.delete(0, END)

    

    
 


root = Tk()
gui = UserInterface(root)

root.mainloop()

