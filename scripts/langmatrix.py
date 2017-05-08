#!/usr/bin/env python3
"""A matrix! Of languages!"""
import nikola.nikola
import os.path
import glob

keys = ['_WINDOWS_LOCALE_GUESSES', 'COLORBOX_LOCALES', 'MOMENTJS_LOCALES', 'PYPHEN_LOCALES', 'DOCUTILS_LOCALES']
keys_short = ['language', 'windows', 'cbox', 'moment', 'pyphen', 'docutils']
print('\t'.join(keys_short))

for tr in nikola.nikola.LEGAL_VALUES['TRANSLATIONS']:
    if isinstance(tr, tuple):
        tr = tr[0]
    out = tr
    if len(out) < 8:
        out += '\t'
    for key in keys:
        out += '\t'
        out += '\x1b[37;42;1m+' if tr in nikola.nikola.LEGAL_VALUES[key] else '\x1b[37;41;1m-'
    print(out + '\x1b[0m')

print('\t'.join(keys_short))
