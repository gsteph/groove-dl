#!/usr/bin/env python
import os
import sys
import shutil

if len(sys.argv) < 2: print "Argument missing."; exit()
dir = sys.argv[1]
sys.argv[1] = "py2exe"

manifest='''<?xml version="1.0" encoding="utf-8"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" />
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.VC90.CRT" version="9.0.21022.8" processorArchitecture="x86" publicKeyToken="1fc8b3b9a1e18e3b"></assemblyIdentity>
    </dependentAssembly>
  </dependency>
</assembly>'''

from distutils.core import setup
import py2exe

setup(
    windows=[{
        "script":"groove.py", 
        "icon_resources": [(1, "../misc/groove.ico")]
            }], 
    console=[{
        "script":"updater.py",
        "other_resources": [(24, 1, manifest)]
            }],
    zipfile="modules\library.zip", 
    options={
        "py2exe":{
            "dist_dir":dir, 
            "optimize": 2,
            "dll_excludes":["w9xpopen.exe", "win32clipboard.pyd", "MPR.dll"], 
            "excludes":["email", "email.utils", "doctest", "pdb", "unittest", "difflib", "inspect"],
            "compressed":False,
            "ignores":["ExampleImages", "ExampleModel", "_scproxy"],
            "ascii":False
                 }
            }
     )
