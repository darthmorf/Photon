from threading import *

# Load classes and functions from shared libs
import sys
sys.path.insert(0, '../Libs')
from photonUtilities import *

class Logger:
    """
    A simple logger to log server actions.

    Attributes:   
    logQueue (photonUtilities.CircularQueue): The queue used for log write commands in the logWriter() method.
    logThread (threading.Thread): The separate thread started for the logger.
    """
    def __init__(self):
        """" Initialises the logger. """
        self.logQueue = CircularQueue(999)
        self.logThread = Thread(target=self.logWriter)
        self.logThread.start()

    def logWriter(self):
        """
        Writes all strings in the queue sequentially.
        Should be run asynchronously.
        """
        while True:
            if not self.logQueue.isEmpty():
                with open("log.txt", "a+") as logFile:
                    logFile.write(self.logQueue.deQueue())

    def log(self, message, enabled=True):
        """ Appends a string to the queue in the correct format. """
        if enabled:
            message = formatDateTime(getDateTime()) + message
            self.logQueue.enQueue(message + "\n")
            print(message)
