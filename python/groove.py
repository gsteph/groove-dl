#!/usr/bin/env python
import httplib
import StringIO
import hashlib
import uuid
import random
import string
import sys
import os
import subprocess
import gzip
import threading
if sys.version_info[1] >= 6:  import json
else: import simplejson as json

_useragent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.56 Safari/536.5"
_token = None

URL = "grooveshark.com" #The base URL of Grooveshark
htmlclient = ('htmlshark', '20120312', 'reallyHotSauce', {"User-Agent":_useragent, "Content-Type":"application/json", "Accept-Encoding":"gzip"}) #This contains all the information connected to the htmlshark client
jsqueue = ['jsqueue', '20120312.08', 'circlesAndSquares']
jsqueue.append({"User-Agent":_useragent, "Referer": 'http://%s/JSQueue.swf?%s' % (URL, jsqueue[1]), "Accept-Encoding":"gzip", "Content-Type":"application/json"}) #This (jsqueue) contains all the information specific to jsqueue

#Setting the static header (Country, session and uuid)
h = {}
h["country"] = {}
h["country"]["CC1"] = 72057594037927940
h["country"]["CC2"] = 0
h["country"]["CC3"] = 0
h["country"]["CC4"] = 0
h["country"]["ID"] = 57
h["country"]["IPR"] = 0
h["privacy"] = 0
h["session"] = (''.join(random.choice(string.digits + string.letters[:6]) for x in range(32))).lower()
h["uuid"] = str.upper(str(uuid.uuid4()))

#The string that is shown when the program loads
entrystring = \
"""A Grooveshark song downloader in python
by George Stephanos <gaf.stephanos@gmail.com>
"""

#Generate a token from the method and the secret string (this the string changes once in a while)
def prepToken(method, secret):
    rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
    return rnd + hashlib.sha1('%s:%s:%s:%s' % (method, _token, secret, rnd)).hexdigest()

#Fetch a queueID (right now we randomly generate it)
def getQueueID():
    return random.randint(1000000000000000000000,99999999999999999999999) #For now this will do

#Get the static token issued by sharkAttack!
def getToken():
    global h, _token
    p = {}
    p["parameters"] = {}
    p["parameters"]["secretKey"] = hashlib.md5(h["session"]).hexdigest()
    p["method"] = "getCommunicationToken"
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    conn = httplib.HTTPSConnection(URL)
    conn.request("POST", "/more.php", json.JSONEncoder().encode(p), htmlclient[3])
    _token = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

#Process a search and return the result as a list.
def getResultsFromSearch(query, what="Songs"):
    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = what
    p["parameters"]["query"] = query
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prepToken("getResultsFromSearch", htmlclient[2])
    p["method"] = "getResultsFromSearch"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), htmlclient[3])
    j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
    try:
        return j["result"]["result"]["Songs"]
    except:
        return j["result"]["result"]

#? Something about artist (probably get's all the songs made by an artist)
def artistGetSongsEx(id, isVerified):
    p = {}
    p["parameters"] = {}
    p["parameters"]["artistID"] = id
    p["parameters"]["isVerifiedOrPopular"] = isVerified
    p["header"] = h
    p["header"]["client"] = htmlclient[0]
    p["header"]["clientRevision"] = htmlclient[1]
    p["header"]["token"] = prepToken("artistGetSongsEx", htmlclient[2])
    p["method"] = "artistGetSongsEx"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), htmlclient[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())

#Get the streamKey used to download the songs off of the servers.
def getStreamKeyFromSongIDs(id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = 8
    p["parameters"]["mobile"] = False
    p["parameters"]["prefetch"] = False
    p["parameters"]["songIDs"] = [id]
    p["parameters"]["country"] = h["country"]
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prepToken("getStreamKeysFromSongIDs", jsqueue[2])
    p["method"] = "getStreamKeysFromSongIDs"
    print json.JSONEncoder().encode(p)
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

#Add a song to the browser queue, used to imitate a browser
def addSongsToQueue(songObj, songQueueID, source = "user"):    
    queueObj = {}
    queueObj["songID"] = songObj["SongID"]
    queueObj["artistID"] = songObj["ArtistID"]
    queueObj["source"] = source
    queueObj["songQueueSongID"] = 1
    
    p = {}
    p["parameters"] = {}
    p["parameters"]["songIDsArtistIDs"] = []
    p["parameters"]["songIDsArtistIDs"].append(queueObj)
    p["parameters"]["songQueueID"] = songQueueID
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prepToken("addSongsToQueue", jsqueue[2])
    p["method"] = "addSongsToQueue"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

#Remove a song from the browser queue, used to imitate a browser, in conjunction with the one above.
def removeSongsFromQueue(songQueueID, userRemoved = True):
    p = {}
    p["parameters"] = {}
    p["parameters"]["songQueueID"] = songQueueID
    p["parameters"]["userRemoved"] = True
    p["parameters"]["songQueueSongIDs"]=[1]
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prepToken("removeSongsFromQueue", jsqueue[2])
    p["method"] = "removeSongsFromQueue"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

#Mark the song as being played more then 30 seconds, used if the download of a songs takes a long time.
def markStreamKeyOver30Seconds(songID, songQueueID, streamServer, streamKey):
    p = {}
    p["parameters"] = {}
    p["parameters"]["songQueueID"] = songQueueID
    p["parameters"]["streamServerID"] = streamServer
    p["parameters"]["songID"] = songID
    p["parameters"]["streamKey"] = streamKey
    p["parameters"]["songQueueSongID"] = 1
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prepToken("markStreamKeyOver30Seconds", jsqueue[2])
    p["method"] = "markStreamKeyOver30Seconds"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

#Mark the song as downloaded, hopefully stopping us from getting banned.
def markSongDownloadedEx(streamServer, songID, streamKey):
    p = {}
    p["parameters"] = {}
    p["parameters"]["streamServerID"] = streamServer
    p["parameters"]["songID"] = songID
    p["parameters"]["streamKey"] = streamKey
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prepToken("markSongDownloadedEx", jsqueue[2])
    p["method"] = "markSongDownloadedEx"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), jsqueue[3])
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

if __name__ == "__main__":
    if len(sys.argv) < 2: #Check if we were passed more than 1 parameters
        import gui
        gui.main() #Open the gui
        exit() #Close the command line
    print entrystring #Print the welcome message
    print "Initializing..."
    getToken() #Get a static token
    i = ' '.join(sys.argv[1:]) #Get the search parameter
    #i = raw_input("Search: ") #Same as above, if you uncomment this, and comment the first 4 lines this can be run entirely from the command line.
    print "Searching for '%s'..." % i
    m = 0
    s = getResultsFromSearch(i) #Get the result from the search
    l = [('%s: "%s" by "%s" (%s)' % (str(m+1), l["SongName"], l["ArtistName"], l["AlbumName"])) for m,l in enumerate(s[:10])] #Iterate over the 10 first returned items, and add a tring to a list.
    if l == []: #If the result was empty print a message and exit
        print "No results found"
        exit()
    else:
        print '\n'.join(l) #Print the results
    songid = raw_input("Enter the Song ID you wish to download or (q) to exit: ") #Ask for input as to what we shoudl download
    if songid == "" or songid == "q": exit() #Exit if choice is empty or q
    songid = eval(songid)-1 #Turn it into an int ans subtract one to fit it to the list index
    queueID = getQueueID() #Get the queue ID
    print "Adding song to player Queue"
    addSongsToQueue(s[songid], queueID) #Add the song to the queue
    print "Retrieving stream key.."
    stream = getStreamKeyFromSongIDs(s[songid]["SongID"]) #Get the StreamKey for the selected song
    for k,v in stream.iteritems():
		stream=v
    if stream == []:
        print "Failed"
        exit()
    print "Starting timer" #Probably not needed, but i if the download takes over 30 seconds, why not? starts a timer that report the song as being played 30 seconds though if the download takes more than 30-35 seconds
    markTimer = threading.Timer(30 + random.randint(0,5), markStreamKeyOver30Seconds, [s[songid]["SongID"], str(queueID), stream["ip"], stream["streamKey"]])
    markTimer.start()
    cmd = 'wget --post-data=streamKey=%s -O "%s - %s.mp3" "http://%s/stream.php"' % (stream["streamKey"], s[songid]["ArtistName"], s[songid]["SongName"], stream["ip"]) #Run wget to download the song
    p = subprocess.Popen(cmd, shell=True)
    try:
        p.wait()#Wait for wget to finish
        print "Marking download as complete"
        markSongDownloadedEx(stream["ip"], s[songid]["SongID"], stream["streamKey"]) #This is the important part, hopefully this will stop grooveshark from banning us (and take the load off their server) Mark the song as being downloaded
    except KeyboardInterrupt: #If we are interrupted by the user
        os.remove('%s - %s.mp3' % (s[songid]["ArtistName"], s[songid]["SongName"])) #Delete the song
        print "Marking download as complete"
        markSongDownloadedEx(stream["ip"], s[songid]["SongID"], stream["streamKey"]) #We do it here to be sure
        print "\nDownload cancelled. File deleted."
    #Natural Exit
