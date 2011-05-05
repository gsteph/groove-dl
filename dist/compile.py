#!/usr/bin/env python
import os
import sys
import shutil

if len(sys.argv) < 2: print "Argument missing."; exit()
dir = sys.argv[1]
sys.argv[1] = "py2exe"

from distutils.core import setup
import py2exe

setup(
    windows=[{
        "script":"groove.py", 
        "icon_resources": [(1, "../misc/groove.ico")]
            }],
    zipfile="modules\library.zip", 
    options={
        "py2exe":{
            "dist_dir":dir, 
            "optimize": 2,
            "dll_excludes":["w9xpopen.exe", "win32clipboard.pyd", "MPR.dll"], 
            "excludes":["email", "doctest", "pdb", "unittest", "difflib", "inspect"],
            "compressed":False,
            "ignores":["ExampleImages", "ExampleModel", "_scproxy"],
            "ascii":False
                 }
            }
     )
