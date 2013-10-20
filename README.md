groove-dl
----------------------------
A downloader to Grooveshark's awesome music library. Based off of the [wiki here](http://nettech.wikia.com/wiki/Grooveshark_Internal_API). For now, only a python version with optional GUI is available.

###Syntax:
CLI: ```groove.py 'query'```

GUI: ```groove.py```

###Dependencies:
* Python 2.6

For GUI:
* [wxPython](http://www.wxpython.org)
* [ObjectListView](http://objectlistview.sourceforge.net/python)

###Windows:
I have packaged installation files for windows (using py2exe + 7z). Get them from the downloads section.

###Linux:
You have to retrieve the dependencies and install them.

###Building EXEs:
My build script (dist.py) is included in the repository under dist/. Should run under latest Wine (with native imagehlp.dll) or Windows. Please do not change the code and distribute until you contact me.

###Ports:
There's a PHP port by Check over at https://github.com/check/groove-php 

###Disclaimer:
I'm not responsible for any violations this script does to Grooveshark's TOS. It's more of a proof of concept.

Python script by George Stephanos <gaf.stephanos@gmail.com>
