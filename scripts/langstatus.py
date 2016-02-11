#!/usr/bin/env python3
import nikola.nikola
import os.path
import glob

used = []
exist = []
for tr in nikola.nikola.LEGAL_VALUES['TRANSLATIONS']:
    if isinstance(tr, tuple):
        used.append(tr[0])
    used.append(tr)

for file in glob.glob(os.path.join('nikola', 'data', 'themes', 'base',
                                   'messages', 'messages_*.py')):
    lang = file.split('_', 1)[1][:-3]
    exist.append(lang)
    if lang in used:
        print('{0}: found'.format(lang))
    elif os.path.islink(file):
        print('\x1b[1;1m\x1b[1;30m{0}: symlink\x1b[0m'.format(lang))
    else:
        print('\x1b[1;1m\x1b[1;31m{0}: NOT found\x1b[0m'.format(lang))
