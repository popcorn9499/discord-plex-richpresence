from plexapi.myplex import MyPlexAccount
from plexapi.alert import AlertListener
import time
import fileIO
import logging
import os


def alertCallback(*args):
    print(args)
    
def alertError(*args):
    print(args)



class Plex:
    conf = {'Plex_User': 'username', 'Plex_Token': 'someToken'}
    
    def __init__(self):
        log = logging.getLogger("Plex")

        fileIO.checkFile("example-conf{0}config.json".format(os.sep),"config.json","config.json",log)

        self.conf = fileIO.fileLoad("config.json")
        
        account = self.login()
    
        print("Auth: "+ account.authenticationToken)
        self.conf["Plex_Token"] = account.authenticationToken
        fileIO.fileSave("config.json", self.conf)
        plex = account.resource("whyNot").connect()
        print("logged in")
        listener = AlertListener(plex,alertCallback, alertError)
        listener.run()

        while(True):
            time.sleep(1)
            print("1")
    
    #Logins into the plex api
    #returns a MyPlexAccount obj or None if something goes wrong
    def login(self, password=None):
        account = None
        try:
            if (password == None):
                account = MyPlexAccount(token=self.conf["Plex_Token"]) 
            else:
                account = MyPlexAccount(self.conf["Plex_User"], password)
        except Exception:
            print("Please provide the username for your plex account or type QUIT and edit config.json directly providing the required fields")
            self.conf["Plex_User"] = input("")
            if (self.conf["Plex_User"] == "QUIT"):
                exit()
            print("Please provide the password for your plex account")
            password = input("")
            account = self.login(password=password)
        return account
    
    
    
x = Plex()
