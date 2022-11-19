from plexapi.myplex import MyPlexAccount, PlexServer
from plexapi.alert import AlertListener
from plexapi.base import Playable, PlexPartialObject
from plexapi.media import Genre, GuidTag
from typing import Optional

import time
import fileIO
import logger 
import os
import threading

from discordRPC import discordRPC

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
    
    timeoutTimer: threading.Timer = None
    plexConnectionTimeoutTimer: threading.Timer = None
    plexConnectionTimeoutInterval: int = 60
    timeoutInterval: int = 30
    playPause = {"playing": "play-circle", "paused": "pause-circle"}
    
    #limits the amount of time the presence stays up when paused
    presenceCount: int = 0
    presenceCountMax: int = 10
    
    
    
    def __init__(self):
        self.log = logger.logs("Plex")
        fileIO.checkFile("example-conf{0}config.json".format(os.sep),"config.json","config.json",self.log)
        self.conf = fileIO.fileLoad("config.json")
        self.discord = discordRPC(self.conf["discordClientID"])
        self.connectPlex()
        for server in self.servers:
            listener = AlertListener(self.servers[server], self.alertCallback, self.alertError)
            listener.run()
        while(True):
            time.sleep(1)
            print("1")
    
    def connectPlex(self):
        self.account = self.login()
        self.log.logger.info("Connecting to plex")
        try: #handle reconnecting since somethings it can't see my server?
            for resource in self.account.resources():
                if resource.product == self._productName:
                    self.log.logger.info("Connecting to " + resource.name)
                    server: MyPlexAccount = resource.connect()
                    self.servers[resource.name] = server
            self.log.logger.info("logged in")
            self.plexConnectionTimeoutTimer = threading.Timer(self.plexConnectionTimeoutInterval, self.connectionHandler)
            self.plexConnectionTimeoutTimer.start()
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
                self.conf["Plex_Token"] = self.account.authenticationToken #get the token and save it to file
                fileIO.fileSave("config.json", self.conf)
        except Exception:
            self.log.logger.info("Please provide the username for your plex account or type QUIT and edit config.json directly providing the required fields")
            self.conf["Plex_User"] = input("")
            if (self.conf["Plex_User"] == "QUIT"):
                exit()
            self.log.logger.info("Please provide the password for your plex account")
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
            self.log.logger.debug("Searching {0} to find the server the session is from. and verify the session key".format(servername))
            if self.isOwner(servername) and sessionServer == None:
                x = server.account()
                self.log.logger.info("HEYO")
                sessions: list[Playable] = server.sessions()
                for session in sessions: #interate through all the sessions on a given server
                    self.log.logger.debug("{0} SessionKey: {1} Usernames: {2}".format(session,session.sessionKey,session.usernames))
                    if session.sessionKey == sessionKey and sessionServer == None: #confirm we are looking at the session that fired the event
                        self.log.logger.debug("Session was found")
                        for sessionUsername in session.usernames: #search usernames to ensure its of the correct userprofile we want.
                            self.log.logger.debug("SessionUser: {0} accountUser: {1}".format(sessionUsername, self.account.username))
                            if sessionUsername == self.account.username:
                                self.log.logger.debug("Found username: {0} same as account user: {1}".format(sessionUsername, self.account.username))
                                sessionServer = server #store the correct name
                                #break
        self.log.logger.info("Returning")
        return sessionServer
    
    def connectionHandler(self):
        try:
            for servername,server in self.servers.items():
                assert server
                self.log.logger.debug("Connection {0} worked".format(servername))
        except Exception as e:
            self.log.logger.error("We lost connection to plex reason {0}".format(e))
            self.connectPlex()
        else:
            self.plexConnectionTimeoutTimer = None
        
    
    def handleTimeout(self):
        self.log.logger.info("Closing discord rpc as we havent needed it for awhile")
        self.lastState, self.lastSessionKey, self.lastRatingKey = "", 0, 0
        self.discord.close()
        self.timeoutTimer.cancel()
        self.timeoutTimer = None
    
    ##all I really care about is playing and pausing

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
                    
                    if state == "stopped":
                        return
                    
                    #this should only be run if we are the owner of that server??
                    sessionServer = self._getSessionServer(sessionKey)
                    
                    #handle a timeout to remove the rpc connection/clear it
                    if self.lastSessionKey == sessionKey and self.lastRatingKey == ratingKey:
                        if self.timeoutTimer:
                            self.timeoutTimer.cancel()
                            self.timeoutTimer = None
                        
                        if self.lastState == state and self.presenceCount < self.presenceCountMax:
                            if state == "paused": #handle limiting the length of time the presence stays up
                                self.presenceCount += 1
                                self.log.logger.info("Presence Paused")
                            self.timeoutTimer = threading.Timer(self.timeoutInterval, self.handleTimeout)
                            self.timeoutTimer.start()
                        elif state == "playing":
                            self.presenceCount = 0
                        else:
                            if state=="stopped" or self.presenceCount >= self.presenceCountMax:
                                self.discord.close()

                    if (sessionServer != None and self.presenceCount < self.presenceCountMax):
                        self.log.logger.info(data)
                        item: PlexPartialObject  = sessionServer.fetchItem(key)
                        print(item)
                        print(item.section())
                        print(item.title)
                        
                        self.lastSessionKey = sessionKey
                        self.lastRatingKey = ratingKey
                        self.lastState = state
                        
                        if item.type=="track":
                            title = item.title
                            grandParentTitle = item.grandparentTitle
                            originalTitle = item.originalTitle
                            parentTitle = item.parentTitle
                            artUrl = item.artUrl
                            posterUrl = item.posterUrl
                            thumbUrl = item.thumbUrl
                            startTime = time.time()
                            endTime = time.time() + ((item.duration - viewOffset)/1000)
                            stateText = f"{originalTitle or grandParentTitle} - {parentTitle} {item.year}"
                            self.log.logger.info("GOING TO PRESENCE")
                            self.discord.setPresence(details=title, state=stateText, large_text="Listening to music", small_image=self.playPause[state], small_text="play-circle", large_image=thumbUrl or "mpd", startTime=startTime, endTime=endTime)
                            self.log.logger.info("PRESENCE DONE")
        
    def alertError(self,*args):
        print(args)
    
x = Plex()
