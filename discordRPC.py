from pypresence import Presence

class discordRPC:
    def __init__(self,client_id):
        self.client_id = client_id
        self.rpc = Presence(self.client_id)
        self.presenceCleared = True
        print("LAUNCHING PRESENCE")
        self.connect()

    def connect(self):
        try:
            self.rpc.connect() 
        except:
            ConnectionErrorDiscordRPC()

    def setPresence(self,state=None,details=None,large_text=None,large_image=None,small_text=None,small_image=None,startTime=None,endTime=None):
        print("Setting presence")
        try:
            self.rpc.update(state=state,details=details,large_text=large_text,large_image=large_image,small_text=small_text,small_image=small_image,start=startTime,end=endTime)
            self.presenceCleared = False
        except:
            self.connect()
            self.setPresence(self,state=state,details=details,large_text=large_text, large_image=large_image,small_text=small_text, small_image=small_image, startTime=startTime, endTime=endTime)
            
    def clear(self):
        if not self.presenceCleared:
            try:
                self.rpc.clear()
                self.presenceCleared = True
            except:
                self.connect()
                

class ConnectionErrorDiscordRPC(Exception):
    pass