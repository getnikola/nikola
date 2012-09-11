"""Utility functions to help you run filters on files."""

import os
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
    command = command.replace('%1', infile)
    command = command.replace('%2', tmpfname)
    subprocess.check_call(command, shell=True)
    shutil.move(tmpfname, infile)


def yui_compressor(infile):
    return runinplace(r'yui-compressor %1 -o %2', infile)
