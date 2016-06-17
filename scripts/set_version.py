#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script to set the version number wherever it's needed before a release."""

from __future__ import unicode_literals, print_function
import io
import os
import re
import sys
import glob
import subprocess
import io


def sed_like_thing(pattern, repl, path):
    """Like re.sub but applies to a file instead of a string."""

    with io.open(path, 'r', encoding='utf8') as inf:
        data = inf.read()

    data = re.sub(pattern, repl, data)

    with io.open(path, 'w+', encoding='utf8') as outf:
        outf.write(data)

if __name__ == "__main__":
    inpf = raw_input if sys.version_info[0] == 2 else input
    while True:
        version = inpf("New version number (in format X.Y.Z): ").strip()
        if version.startswith('v'):
            print("ERROR: the version number must not start with v.")
        else:
            break

    for doc in glob.glob(os.path.join("docs/*.txt")):
        sed_like_thing(":Version: .*", ":Version: {0}".format(version), doc)

    sed_like_thing("version='.+'", "version='{0}'".format(version), 'setup.py')
    sed_like_thing("version = .*", "version = '{0}'".format(version), os.path.join('docs', 'sphinx', 'conf.py'))
    sed_like_thing("release = .*", "release = '{0}'".format(version), os.path.join('docs', 'sphinx', 'conf.py'))
    sed_like_thing('__version__ = ".*"', '__version__ = "{0}"'.format(version), os.path.join('nikola', '__init__.py'))
    sed_like_thing('New in master', 'New in v{0}'.format(version), 'CHANGES.txt')
    sed_like_thing(':Version: .*', ':Version: Nikola v{0}'.format(version), os.path.join('docs', 'man', 'nikola.rst'))
    sed_like_thing('version: .*', 'version: {}'.format(version), 'snapcraft/snapcraft.yaml')
    sed_like_thing('source-tag: .*', 'source-tag: {}'.format(version), 'snapcraft/snapcraft.yaml')
    sed_like_thing('Nikola==.*\'', 'Nikola=={}\''.format(version), 'snapcraft/nikola.py')
    man = subprocess.check_output(["rst2man.py", os.path.join('docs', 'man', 'nikola.rst')])
    with io.open(os.path.join('docs', 'man', 'nikola.1'), 'w', encoding='utf-8') as fh:
        try:
            man = man.decode('utf-8')
        except AttributeError:
            pass
        fh.write(man)
    subprocess.call(["gzip", "-f", os.path.join('docs', 'man', 'nikola.1')])
