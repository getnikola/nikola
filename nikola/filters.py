# Copyright (c) 2012 Roberto Alsina y otros.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Utility functions to help you run filters on files."""

import os
import re
import shutil
import subprocess
import tempfile


def runinplace(command, infile):
    """Runs a command in-place on a file.

    command is a string of the form: "commandname %1 %2" and
    it will be execed with infile as %1 and a temporary file
    as %2. Then, that temporary file will be moved over %1.

    Example usage:

    runinplace("yui-compressor %1 -o %2", "myfile.css")

    That will replace myfile.css with a minified version.

    """

    tmpdir = tempfile.mkdtemp()
    tmpfname = os.path.join(tmpdir, os.path.basename(infile))
    command = command.replace('%1', "'%s'" % infile)

    needs_tmp = "%2" in command
    command = command.replace('%2', "'%s'" % tmpfname)

    subprocess.check_call(command, shell=True)

    if needs_tmp:
        shutil.move(tmpfname, infile)


def yui_compressor(infile):
    return runinplace(r'yui-compressor --nomunge %1 -o %2', infile)


def optipng(infile):
    return runinplace(r"optipng -preserve -o2 -quiet %1", infile)


def jpegoptim(infile):
    return runinplace(r"jpegoptim -p --strip-all -q %1", infile)


def tidy(inplace):
    # Goggle site verifcation files are no HTML
    if re.match(r"google[a-f0-9]+.html", os.path.basename(inplace)) \
            and open(inplace).readline().startswith(
                "google-site-verification:"):
        return

    # Tidy will give error exits, that we will ignore.
    output = subprocess.check_output("tidy -m -w 90 --indent no --quote-marks"
                                     "no --keep-time yes --tidy-mark no "
                                     "--force-output yes '{0}'; exit 0".format(
                                     inplace), stderr=subprocess.STDOUT,
                                     shell=True)

    for line in output.split("\n"):
        if "Warning:" in line:
            if '<meta> proprietary attribute "charset"' in line:
                # We want to set it though.
                continue
            elif '<meta> lacks "content" attribute' in line:
                # False alarm to me.
                continue
            elif '<div> anchor' in line and 'already defined' in line:
                # Some seeming problem with JavaScript terminators.
                continue
            elif '<img> lacks "alt" attribute' in line:
                # Happens in gallery code, probably can be tolerated.
                continue
            elif '<table> lacks "summary" attribute' in line:
                # Happens for tables, TODO: Check this is normal.
                continue
            elif 'proprietary attribute "data-toggle"' in line or \
                 'proprietary attribute "data-target"':
                # Some of our own tricks
                continue
            else:
                assert False, (inplace, line)
        elif "Error:" in line:
            if '<time> is not recognized' in line:
                # False alarm, time is proper HTML5.
                continue
            else:
                assert False, line
