import json
import os.path

class ConfigManager():
    def __init__(self, file, defaultData):
        self.data = self.loadJson(file)
        if self.data == None:
            self.initJson(file, defaultData)
            self.data = self.loadJson(file)

    def loadJson(self, file):        
        if os.path.isfile(file):
            with open(file, "r") as jsonFile:
                return json.load(jsonFile)
        else:
            return None

    def initJson(self, file, defaultData):        
        jsonString = json.dumps(defaultData)
        with open(file, "w") as jsonFile:
            jsonFile.write(jsonString)


class ServerConfig(ConfigManager):
    def __init__(self, file):
        self.defaultData = {

            "dbFile": "photon.db",
            "infoLoggingEnabled": True,
            "maxTransmissionSize": 40960,
            "port": 9998

            }
            
        super().__init__(file, self.defaultData)


class ClientConfig(ConfigManager):
    def __init__(self, file):
        self.defaultData = {

            "maxTransmissionSize": 40960,
            "debug": True,
            "commandChar": "/",
            "port": 9998

            }

        super().__init__(file, self.defaultData)
