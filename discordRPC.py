from pypresence import Presence
import logger 

class discordRPC:
    log: logger.logs = None 
    connected: bool = False
    
    def __init__(self,client_id):
        self.log = logger.logs("Discord RPC")
        self.client_id = client_id
        self.rpc = Presence(self.client_id)
        self.presenceCleared = True
        self.log.logger.info("LAUNCHING PRESENCE")
        self.connect()
        self.connected=True

    def connect(self):
        try:
            self.log.logger.info("Attempting presence reconnection")
            if (not self.connected):
                self.rpc.connect()
                self.connected = True 
        except:
            self.log.logger.info("Reconnection error")
            ConnectionErrorDiscordRPC()

    def setPresence(self,state=None,details="",large_text=None,large_image=None,small_text=None,small_image=None,startTime=None,endTime=None):
        self.log.logger.info("Setting presence")
        if details == "": #handle preventing details from being empty string
            details = "N/A"
        try:
            self.connect()
            self.rpc.update(state=state,details=details,large_text=large_text,large_image=large_image,small_text=small_text,small_image=small_image,start=startTime,end=endTime)
            self.presenceCleared = False
        except Exception as e:
            print(e)
            self.connect()
            self.setPresence(self,state=state,details=details,large_text=large_text, large_image=large_image,small_text=small_text, small_image=small_image, startTime=startTime, endTime=endTime)
            
    def clear(self):
        if not self.presenceCleared:
            self.log.logger.info("Clearing presence")
            try:
                self.rpc.clear()
                self.presenceCleared = True
            except:
                self.connect()
                
    def close(self):
        self.log.logger.info("Closing presence")
        if (self.connected):
            self.rpc.clear()
            self.rpc.close()
            self.connected=False

class ConnectionErrorDiscordRPC(Exception):
    pass