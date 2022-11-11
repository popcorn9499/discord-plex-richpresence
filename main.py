from plexapi.myplex import MyPlexAccount, PlexServer
from plexapi.alert import AlertListener
from plexapi.base import Playable, PlexPartialObject
from plexapi.media import Genre, GuidTag
from typing import Optional

import time
import fileIO
import logger 
import os






class Plex:
    _productName = "Plex Media Server" #used to allow us to sort only by specific products
    conf = {'Plex_User': 'username', 'Plex_Token': 'someToken'}
    account: MyPlexAccount = None #should be type MyPlexAccount
    log: logger.logs = None #Logging object
    servers: dict[str,PlexServer] = {}
    
    #temp variable
    lastSessionKey = None
    lastRatingKey = None
    lastState = None
    
    def __init__(self):
        self.log = logger.logs("Plex")
        fileIO.checkFile("example-conf{0}config.json".format(os.sep),"config.json","config.json",self.log)

        self.conf = fileIO.fileLoad("config.json")
        
        self.account = self.login()
    
        self.conf["Plex_Token"] = self.account.authenticationToken
        fileIO.fileSave("config.json", self.conf)
        self.log.logger.info("Connecting to plex")
        self.connectPlex()
        print("logged in")
        for server in self.servers:
            listener = AlertListener(self.servers[server], self.alertCallback, self.alertError)
            listener.run()

        while(True):
            time.sleep(1)
            print("1")
    
    def connectPlex(self):
        try: #handle reconnecting since somethings it can't see my server?
            for resource in self.account.resources():
                if resource.product == self._productName:
                    self.log.logger.info("Connecting to " + resource.name)
                    server: MyPlexAccount = resource.connect()
                    self.servers[resource.name] = server
        except Exception:
            self.log.info("Retrying to find plex server")
            self.connectPlex()
    
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
    
    
    def isOwner(self,serverName):
        result = False
        try:
            self.servers[serverName].account()
            result = True
        except:
            self.log.logger.info("Not the owner")
            pass
        return result
    
    def _getSessionServer(self,sessionKey: int):
        sessionServer = None
        for servername,server in self.servers.items(): #ensures we search every server for the actual server that the session is from
            self.log.logger.info("Searching {0} to find the server the session is from. and verify the session key".format(servername))
            if self.isOwner(servername) and sessionServer == None:
                if servername == "monka":
                    print("NOT OWNERRR")
                x = server.account()
                print("HEYO")
                sessions: list[Playable] = server.sessions()
                for session in sessions: #interate through all the sessions on a given server
                    self.log.logger.info("{0} SessionKey: {1} Usernames: {2}".format(session,session.sessionKey,session.usernames))
                    if session.sessionKey == sessionKey and sessionServer == None: #confirm we are looking at the session that fired the event
                        self.log.logger.debug("Session was found")
                        for sessionUsername in session.usernames: #search usernames to ensure its of the correct userprofile we want.
                            self.log.logger.info("SessionUser: {0} accountUser: {1}".format(sessionUsername, self.account.username))
                            if sessionUsername == self.account.username:
                                self.log.logger.info("Found username: {0} same as account user: {1}".format(sessionUsername, self.account.username))
                                sessionServer = server #store the correct name
                                #break
        print("Returning")
        return sessionServer
    
    ##all I really care about is playing and pausing
    #({'type': 'playing', 'size': 1, 'PlaySessionStateNotification': [{'sessionKey': '2', 'clientIdentifier': '88b4f7f6-7554-4338-8982-a044a3a7d010', 'guid': '', 'ratingKey': '147967', 'url': '', 'key': '/library/metadata/147967', 'viewOffset': 4910, 'playQueueItemID': 576940, 'playQueueID': 14462, 'state': 'paused'}]},)
    def alertCallback(self,*args):
        for data in args:
            if (data["type"] == "playing" and "PlaySessionStateNotification" in data):
                #print(data)
                for session in data["PlaySessionStateNotification"]:
                    key = session["key"]
                    ratingKey = int(session["ratingKey"])
                    viewOffset = int(session["viewOffset"]) #stored in ms
                    state = session["state"]
                    sessionKey = int(session["sessionKey"])
                    
                    sessionServer: PlexServer = None
                    artUrl = None
                    posterUrl = None
                    thumbUrl = None
                    title = None #title of the track of music
                    parentTitle = None #usually album for music
                    grandParentTitle = None #sometimes artist?
                    originalTitle = None
                    #handle disconnecting the rpc. handle a threaded timer potentially?
                    
                    
                    if state == "stopped":
                        return
                    
                    #handle getting the session from the servers
                    
                    #this should only be run if we are the owner of that server??
                    sessionServer = self._getSessionServer(sessionKey)
                    
                    print("IM HEREEE")

                    if (sessionServer != None):
                        self.log.logger.info(data)
                        item: PlexPartialObject  = sessionServer.fetchItem(key)
                        print(item)
                        print(item.section())
                        print(item.title)
                        title = item.title
                        grandParentTitle = item.grandparentTitle
                        originalTitle = item.originalTitle
                        parentTitle = item.parentTitle
                        artUrl = item.artUrl
                        posterUrl = item.posterUrl
                        thumbUrl = item.thumbUrl
                    print("END")

        
    def alertError(self,*args):
        print(args)
            
    
x = Plex()
