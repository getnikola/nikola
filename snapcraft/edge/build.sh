#!/bin/sh
snapcraft
cp ../nikola.py prime/usr/bin/nikola
find prime/ -name '*.a' -exec rm {} \;
snapcraft

