# Server.py file

import socket                                         
from threading import Thread
import pickle as p


# Global Variables
ClientCount = 0
Messages = ["<Server>: Hello", "<Server>: World"]
Clients  = []
Threads  = []

# Threads
def ClientConnected(clientSocket, address): # New thread instance created for each connected client
   try:
      global Messages
      
      print("Got a connection from " + str(address))
      clientSocket.send(p.dumps(Messages)) # Send list of all previous messages to client
      ListenForPackets(clientSocket)
         
   except Exception as e:
      print(str(e))


def ListenForPackets(clientSocket):
   global Messages
   while True:
         response = p.loads(clientSocket.recv(1024)) # Wait for message from new client
         Messages.append(response)
         SendToClients(response)

         
def SendToClients(message):
   global Clients
   
   for client in Clients:
      client.send(p.dumps(message))


def __main__():
   # Create a socket object
   serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

   # Get local machine name
   host = socket.gethostname()                           
   port = 9999                                           

   # Bind to the port
   serverSocket.bind((host, port))

   # Queue up to 5 requests
   serverSocket.listen(5)                                           
   print("\nListening for connections...")
   
   while True:
      # Waiting for connections
      clientSocket, clientAddress = serverSocket.accept()
      Clients.append(clientSocket)
      newThread = Thread(target=ClientConnected, args=(clientSocket, clientAddress))
      newThread.start()
      Threads.append(newThread)


if __name__ == "__main__":
   __main__()
