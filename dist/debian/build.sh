#!/bin/sh
echo "2.0" > debian-binary
cp ../../python/groove.py ./data/usr/lib/groove-dl/groove.py
cp ../../python/gui.py ./data/usr/lib/groove-dl/gui.py
tar --mode=755 -hcC control `ls control` > control.tar
tar --mode=755 -hcC data `ls data` > data.tar
python assist.py control.tar
python assist.py data.tar
python assist.py version
gzip control.tar
gzip data.tar
ar -rc $1 debian-binary control.tar.gz data.tar.gz
rm control.tar.gz
rm data.tar.gz
rm debian-binary
