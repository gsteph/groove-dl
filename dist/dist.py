#!/usr/bin/env python
import sys
import os
import shutil
import subprocess
shutil.copyfile('../python/gui.py', './gui.py')
shutil.copyfile('../python/groove.py', './groove.py')
exec(open("gui.py", "r").read().split('\n')[1])
dir = "files/groove-dl_%sall/" % version
cmdbuild = ["python", "%s/compile.py" % os.getcwd(), "%s" % dir]
shutil.rmtree(dir, True)
shutil.rmtree("build", True)
shutil.rmtree("files/groove-dl_%s.exe" % version, True) 
if sys.platform == "linux2": cmdbuild = ["wine"] + cmdbuild
try: os.makedirs(dir)
except: pass
shutil.copyfile("../misc/readme.txt", dir + "readme.txt")
filename = dir.split("/")[1]
cmdarchive = '7z a -t7z ../%s.7z *' % filename
cmdnsis = ['C:\Program Files (x86)\NSIS\makensis.exe', '/DOUTFILE=files\groove-dl_%sall.exe' % version, '/DVERSION=%s' % version, '/DSETUPDIR=%s' % os.path.abspath(dir), 'groove-dl.nsi']

if sys.platform == "win32":
    cmdmerge = 'copy /b "..\\..\\misc\\7zsd.sfx\"+..\\..\\misc\\sfxconfig.txt+groove-dl_%sall.7z %s.exe' % (version, filename)
if sys.platform == "linux2":
    cmdmerge = "cat ../../misc/7zsd.sfx ../../misc/sfxconfig.txt groove-dl_%sall.7z > %s.exe" % (version, filename)
try:
    p = subprocess.Popen(cmdbuild, cwd=os.getcwd())
    os.chdir(dir)
    print ' '.join(cmdbuild); assert p.wait() == 0
    os.system('upx -9 *.exe *.dll modules\\*.pyd modules\\*.dll')
    os.chdir('../..')
    p = subprocess.Popen(cmdnsis, cwd=os.getcwd())
    print ' '.join(cmdnsis); assert p.wait() == 0
    #print cmdarchive; assert os.system(cmdarchive) == 0
    #os.chdir('..')
    #print os.getcwd()
    #print cmdmerge; assert os.system(cmdmerge) == 0
    #os.remove(filename + ".7z")
except:
    print "Failed."
