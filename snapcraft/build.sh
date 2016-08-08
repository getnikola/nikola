#!/bin/sh
snapcraft
cp nikola.py stage/usr/bin/nikola
find prime/ -name '*.a' -exec rm {} \;
snapcraft

