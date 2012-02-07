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

_useragent = "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"
_referer = "http://grooveshark.com/JSQueue.swf?20110725.01"
_token = None

h = {}
h["country"] = {}
h["country"]["CC1"] = "0"
h["country"]["CC2"] = "0"
h["country"]["CC3"] = "0"
h["country"]["CC4"] = "0"
h["country"]["ID"] = "1"
h["privacy"] = 0
h["session"] = None
h["uuid"] = str.upper(str(uuid.uuid4()))

entrystring = \
"""A Grooveshark song downloader in python
by George Stephanos <gaf.stephanos@gmail.com>
"""

def prepToken(method, secret):
    rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
    return rnd + hashlib.sha1(method + ":" + _token + secret + rnd).hexdigest()

def getToken():
    global h, _token
    p = {}
    p["parameters"] = {}
    p["parameters"]["secretKey"] = hashlib.md5(h["session"]).hexdigest()
    p["method"] = "getCommunicationToken"
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20110906"
    conn = httplib.HTTPSConnection("grooveshark.com")
    conn.request("POST", "/more.php", json.JSONEncoder().encode(p), {"User-Agent": _useragent, "Referer": _referer, "Content-Type":"", "Accept-Encoding":"gzip", "Cookie":"PHPSESSID=" + h["session"]})
    _token = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

def getResultsFromSearch(query, what="Songs"):
    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = what
    p["parameters"]["query"] = query
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20110906"
    p["header"]["token"] = prepToken("getResultsFromSearch", ":imOnAHorse:")
    p["method"] = "getResultsFromSearch"
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), 
								 {"User-Agent": _useragent, 
								  "Referer":"http://grooveshark.com/", 
								  "Content-Type":"application/json", 
								  "Accept-Encoding":"gzip", 
								  "Cookie":"PHPSESSID=" + h["session"]})
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
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20110906"
    p["header"]["token"] = prepToken("artistGetSongsEx", ":imOnAHorse:")
    p["method"] = "artistGetSongsEx"
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"User-Agent": _useragent, "Referer": _referer, "Content-Type":"", "Accept-Encoding":"gzip", "Cookie":"PHPSESSID=" + h["session"]})
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())

def getStreamKeyFromSongIDEx(id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["mobile"] = "false"
    p["parameters"]["prefetch"] = "false"
    p["parameters"]["songIDs"] = id
    p["parameters"]["country"] = h["country"]
    p["header"] = h
    p["header"]["client"] = "jsqueue"
    p["header"]["clientRevision"] = "20110906.04"
    p["header"]["token"] = prepToken("getStreamKeysFromSongIDs", ":theTicketsAreNowDiamonds:")
    p["method"] = "getStreamKeysFromSongIDs"
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"User-Agent": _useragent, "Referer": _referer, "Accept-Encoding":"gzip", "Content-Type":"", "Cookie":"PHPSESSID=" + h["session"]})
    j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
    return j

def header_cb(buf):
    global h
    if "PHPSESSID" in buf:
        buf = buf.split(' ')
        h["session"] = buf[1][10:-1]

def init():
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("HEAD", "", headers={"User-Agent": _useragent})
    res = conn.getresponse()
    cookie = res.getheader("set-cookie").split(";")
    h["session"] = cookie[0][10:]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        import gui
        gui.main()
        exit()
    print entrystring
    init()
    getToken()
    m = 0
    s = getResultsFromSearch(sys.argv[1])
    for l in s:
        m += 1
        print str(m) + ': "' + l["SongName"] + '" by "' + l["ArtistName"] + '" (' + l["AlbumName"] + ')'
        if m == 10: break
    songid = raw_input("Enter the Song ID you wish to download or (q) to exit: ")
    if songid == "" or songid == "q": exit()
    songid = eval(songid)
    stream = getStreamKeyFromSongIDEx(s[songid]["SongID"])
    for k,v in stream["result"].iteritems():
		stream=v
    s =  'wget --user-agent="%s" --referer=%s --post-data=streamKey=%s -O "%s - %s.mp3" "http://%s/stream.php"' % (_useragent, _referer, stream["streamKey"], s[songid]["ArtistName"], s[songid]["SongName"], stream["ip"])
    p = subprocess.Popen(s, shell=True)
    p.wait()
