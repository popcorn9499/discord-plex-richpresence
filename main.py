from plexapi.myplex import MyPlexAccount
from plexapi.alert import AlertListener
import time

def alertCallback(*args):
    print(args)
    
def alertError(*args):
    print(args)

account = MyPlexAccount("popcorn9499@gmail.com", 'x') 

plex = account.resource("whyNot").connect()
print("logged in")
listener = AlertListener(plex,alertCallback, alertError)
listener.run()

while(True):
        time.sleep(1)
        print("1")