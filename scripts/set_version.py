#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script to set the version number wherever it's needed before a release."""

from __future__ import unicode_literals, print_function
import codecs
import os
import re
import sys
import glob


def sed_like_thing(pattern, repl, path):
    """Like re.sub but applies to a file instead of a string."""

    with codecs.open(path, 'rb', 'utf8') as inf:
        data = inf.read()

    data = re.sub(pattern, repl, data)

    with codecs.open(path, 'wb+', 'utf8') as outf:
        outf.write(data)

if __name__ == "__main__":
    print("New version number: ", end="")
    sys.stdout.flush()
    version = sys.stdin.readline().strip()

    for doc in glob.glob(os.path.join("docs/*.txt")):
        sed_like_thing(":Version: .*", ":Version: {0}".format(version), doc)

    sed_like_thing("version='.+'", "version='{0}'".format(version), 'setup.py')
    sed_like_thing("version = '.+'", "version = '{0}'".format(version), os.path.join('docs', 'sphinx', 'conf.py'))
    sed_like_thing("release = '.+'", "release = '{0}'".format(version), os.path.join('docs', 'sphinx', 'conf.py'))
    sed_like_thing('__version__ = ".*"', '__version__ = "{0}"'.format(version), os.path.join('nikola', '__init__.py'))
    sed_like_thing('New in Master', 'New in {0}'.format(version), 'CHANGES.txt')
    os.system("help2man -h help -N --version-string='{0}' nikola > {1}".format(version, os.path.join('docs', 'man', 'nikola.1')))
