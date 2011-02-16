#!/usr/bin/env python
import sys
import os
import shutil
import subprocess
exec(open("gui.py", "r").read().split('\n')[1])
dir = "files/groove-dl_%sall/" % version
cmdbuild = "python %s/compile.py %s" % (os.getcwd(), dir)
if sys.platform == "linux2": cmdbuild = "wine " + cmdbuild
try: os.makedirs(dir)
except: pass
shutil.copyfile("../misc/readme.txt", dir + "readme.txt")
filename = dir.split("/")[1]
cmdarchive = '7z a -t7z ../%s.7z *' % filename
#cmdicon = 'rcedit.exe /I groove-dl_%sall.exe ../../misc/groove.ico' % version

if sys.platform == "win32":
    cmdmerge = 'copy /b "..\\..\\misc\\7zsd.sfx\"+..\\..\\misc\\sfxconfig.txt+groove-dl_%sall.7z %s.exe' % (version, filename)
if sys.platform == "linux2":
    cmdmerge = "cat ../../misc/7zsd.sfx ../../misc/sfxconfig.txt groove-dl_%sall.7z > %s.exe" % (version, filename)
    #cmdicon = "wine " + cmdicon
try:
    p = subprocess.Popen(cmdbuild.split(), cwd=os.getcwd())
    os.chdir(dir)
    print cmdbuild; assert p.wait() == 0
    print cmdarchive; assert os.system(cmdarchive) == 0
    os.chdir('..')
    print os.getcwd()
    print cmdmerge; assert os.system(cmdmerge) == 0
    #print cmdicon; assert os.system(cmdicon) == 0
    os.remove(filename + ".7z")
except:
    print "Failed."
