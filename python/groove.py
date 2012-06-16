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
if sys.version_info[1] >= 6:  import json
else: import simplejson as json

_useragent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"
_token = None

URL = "grooveshark.com"
htmlclient = ('htmlshark', '20120312', 'reallyHotSauce')
jsqueue = ('jsqueue', '20120312.08', 'circlesAndSquares')

h = {}
h["country"] = {}
h["country"]["CC1"] = 0
h["country"]["CC2"] = 0
h["country"]["CC3"] = 0
h["country"]["CC4"] = 0
h["country"]["ID"] = 1
h["country"]["IPR"] = 0
h["privacy"] = 0
h["session"] = (''.join(random.choice(string.digits + string.letters[:6]) for x in range(32))).lower()
h["uuid"] = str.upper(str(uuid.uuid4()))

entrystring = \
"""A Grooveshark song downloader in python
by George Stephanos <gaf.stephanos@gmail.com>
"""

def prepToken(method, secret):
    rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
    return rnd + hashlib.sha1('%s:%s:%s:%s' % (method, _token, secret, rnd)).hexdigest()

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
    conn.request("POST", "/more.php", json.JSONEncoder().encode(p), {"Content-Type":"", "Accept-Encoding":"gzip"})
    _token = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

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
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"Content-Type":"application/json", "Accept-Encoding":"gzip"})
    j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
    try:
        return j["result"]["result"]["Songs"]
    except:
        return j["result"]["result"]

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
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"Content-Type":"", "Accept-Encoding":"gzip"})
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())

def getStreamKeyFromSongIDs(id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = 0
    p["parameters"]["mobile"] = False
    p["parameters"]["prefetch"] = False
    p["parameters"]["songIDs"] = [id]
    p["parameters"]["country"] = h["country"]
    p["header"] = h
    p["header"]["client"] = jsqueue[0]
    p["header"]["clientRevision"] = jsqueue[1]
    p["header"]["token"] = prepToken("getStreamKeysFromSongIDs", jsqueue[2])
    p["method"] = "getStreamKeysFromSongIDs"
    conn = httplib.HTTPConnection(URL)
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"Referer": 'http://%s/JSQueue.swf?%s' % (URL, jsqueue[1]), "Accept-Encoding":"gzip", "Content-Type":"application/json"})
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        import gui
        gui.main()
        exit()
    print entrystring
    print "Initializing..."
    getToken()
    i = ' '.join(sys.argv[1:])
    print "Searching for '%s'..." % i
    m = 0
    s = getResultsFromSearch(i)
    l = [('%s: "%s" by "%s" (%s)' % (str(m+1), l["SongName"], l["ArtistName"], l["AlbumName"])) for m,l in enumerate(s[:10])]
    if l == []:
        print "No results found"
        exit()
    else:
        print '\n'.join(l)

    songid = raw_input("Enter the Song ID you wish to download or (q) to exit: ")
    if songid == "" or songid == "q": exit()
    songid = eval(songid)-1
    print "Retrieving stream key.."
    stream = getStreamKeyFromSongIDs(s[songid]["SongID"])
    for k,v in stream.iteritems():
		stream=v
    if stream == []:
        print "Failed"
        exit()
    cmd = 'wget --post-data=streamKey=%s -O "%s - %s.mp3" "http://%s/stream.php"' % (stream["streamKey"], s[songid]["ArtistName"], s[songid]["SongName"], stream["ip"])
    p = subprocess.Popen(cmd, shell=True)
    try:
        p.wait()
    except KeyboardInterrupt:
        os.remove('%s - %s.mp3' % (s[songid]["ArtistName"], s[songid]["SongName"]))
        print "\nDownload cancelled. File deleted."
