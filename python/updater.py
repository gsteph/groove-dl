#!/usr/bin/env python
import sys
import urllib
import time
url = sys.argv[1]
def progress(per):
    sys.stdout.write("\r")
    sys.stdout.write("[")
    for j in range(0,per/2):
        sys.stdout.write("=")
    for j in range(per/2,50):
        sys.stdout.write(" ")
    sys.stdout.write("] %d%%" % per)
    sys.stdout.flush()
def updatehook(countBlocks, Block, TotalSize):
    progress(int(float(countBlocks*Block)/float(TotalSize)*100))

print "Downloading %s" % url.split('/')[-1]
filename = urllib.urlretrieve(url, reporthook=updatehook)[0]
sys.stdout.write("\n")

newfile = filename+"tmp.exe"
o = open(newfile, "wb")
for l in open(filename, "rb"):                                         ### Hack to replace the extract path
    if "InstallPath" in l:                                             ### to the current directory
        l = l[:12] + '"' + os.getcwd().replace('\\', '\\\\') + '"\n'   ### because the functionality doesn't
    o.write(l)                                                         ### exist yet in 7zsfx through CLI
o.close()
os.startfile(newfile + " -ai -gm2 -y")
