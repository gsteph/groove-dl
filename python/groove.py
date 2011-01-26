#!/usr/bin/env python
import httplib
import StringIO
import json
import hashlib
import uuid
import random
import string
import sys
import os
import subprocess

_useragent = "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"
_token = None

h = {}
h["Country"] = {}
h["Country"]["CC1"] = "0"
h["Country"]["CC2"] = "0"
h["Country"]["CC3"] = "0"
h["Country"]["CC4"] = "0"
h["Country"]["ID"] = "1"
h["privacy"] = 0
h["session"] = None
h["uuid"] = str(uuid.uuid4())

def prepToken(method):
    rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
    return rnd + hashlib.sha1(method + ":" + _token + ":quitStealinMahShit:" + rnd).hexdigest()

def getToken():
    global h, _token
    p = {}
    p["parameters"] = {}
    p["parameters"]["secretKey"] = hashlib.md5(h["session"]).hexdigest()
    p["method"] = "getCommunicationToken"
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20100831"
    headers={"User-Agent": _useragent, "Content-Type":"", "Cookie":"PHPSESSID=" + h["session"]}
    conn = httplib.HTTPSConnection("retrocowbell.grooveshark.com")
    conn.request("POST", "/service.php", json.JSONEncoder().encode(p))
    res = conn.getresponse()
    _token = json.JSONDecoder().decode(res.read())["result"]

def getSearchResultsEx(query, type="Songs"):
    p = {}
    p["parameters"] = {}
    p["parameters"]["limit"] = 25
    p["parameters"]["offset"] = 1
    p["parameters"]["type"] = type
    p["parameters"]["query"] = query
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20100831"
    p["header"]["token"] = prepToken("getSearchResultsEx")
    p["method"] = "getSearchResultsEx"
    headers={"User-Agent": _useragent, "Content-Type":"", "Cookie":"PHPSESSID=" + h["session"]}
    conn = httplib.HTTPConnection("listen.grooveshark.com")
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p))
    res = conn.getresponse()
    result = json.JSONDecoder().decode(res.read())
    result = result["result"]["result"]
    return result

def getStreamKeyFromSongIDEx(id):
    p = {}
    p["parameters"] = {}
    p["parameters"]["mobile"] = "false"
    p["parameters"]["prefetch"] = "false"
    p["parameters"]["songID"] = id
    p["parameters"]["country"] = h["Country"]
    p["header"] = h
    p["header"]["client"] = "jsqueue"
    p["header"]["clientRevision"] = "20101012.37"
    p["header"]["token"] = prepToken("getStreamKeyFromSongIDEx")
    p["method"] = "getStreamKeyFromSongIDEx"

    headers={"User-Agent": _useragent, "Content-Type":"", "Cookie":"PHPSESSID=" + h["session"]}
    conn = httplib.HTTPConnection("listen.grooveshark.com")
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p))
    res = conn.getresponse()
    return json.JSONDecoder().decode(res.read())

def header_cb(buf):
    global h
    if "PHPSESSID" in buf:
        buf = buf.split(' ')
        h["session"] = buf[1][10:-1]

def init():
    conn = httplib.HTTPConnection("listen.grooveshark.com")
    conn.request("HEAD", "", headers={"User-Agent": _useragent})
    res = conn.getresponse()
    cookie = res.getheader("set-cookie").split(";")
    h["session"] = cookie[0][10:]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Query Required"
        exit()
    init()
    getToken()
    m = 0
    s = getSearchResultsEx(sys.argv[1])
    for l in s:
        m += 1
        print str(m) + ': "' + l["SongName"] + '" by "' + l["ArtistName"] + '" (' + l["AlbumName"] + ')'
        if m == 10: break
    songid = raw_input("Enter the Song ID you wish to download or (q) to exit: ")
    if songid == None or songid == "q": exit()
    songid = eval(songid)
    stream = getStreamKeyFromSongIDEx(s[songid]["SongID"])
    s =  'wget --post-data=streamKey=%s -O "%s - %s.mp3" "http://%s/stream.php"' % (stream["result"]["streamKey"], s[songid]["ArtistName"], s[songid]["SongName"], stream["result"]["ip"])
    p = subprocess.Popen(s, shell=True)
    p.wait()
