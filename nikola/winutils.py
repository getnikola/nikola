# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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

"""windows utilities to workaround problems with symlinks in a git clone"""

import os
import shutil
import sys
# don't add imports outside stdlib, will be imported in setup.py


def should_fix_git_symlinked():
    """True if git symlinls markers should be filled with the real content"""
    if sys.platform == 'win32':
        path = (os.path.dirname(__file__) +
                r'\data\samplesite\stories\theming.rst')
        try:
            if os.path.getsize(path) < 200:
                return True
        except Exception:
            pass
    return False


def fix_git_symlinked(src, dst):
    """fix git symlinked files in windows that had been copied from src to dst

    Most (all?) of git implementations in windows store a symlink pointing
    into the repo as a text file, the text being the relative path to the
    file with the real content.

    So, in a clone of nikola in windows the symlinked files will have the
    wrong content.

    The linux usage pattern for those files is 'copy to some dir, then use',
    so we inspect after the copy and rewrite the wrong contents.

    The goals are:
       support running nikola from a clone without installing and without
       making dirty the WC.

       support install from the WC.

       if possible and needed, support running the test suite without making
       dirty the WC.
    """
    # if running from WC there should be a 'doc' dir sibling to nikola package
    if not should_fix_git_symlinked():
        return
    # probabbly in a WC, so symlinks should be fixed
    for root, dirs, files in os.walk(dst):
        for name in files:
            filename = os.path.join(root, name)

            # detect if symlinked
            try:
                if not (2 < os.path.getsize(filename) < 500):
                    continue
                # which encoding uses a git symlink marker ? betting on default
                with open(filename, 'r') as f:
                    text = f.read()
                if text[0] != '.':
                    # de facto hint to skip binary files and exclude.meta
                    continue
            except Exception:
                # probably encoding: content binary or encoding not defalt,
                # also in py2.6 it can be path encoding
                continue
            dst_dir_relpath = os.path.dirname(os.path.relpath(filename, dst))
            path = os.path.normpath(os.path.join(src, dst_dir_relpath, text))
            if not os.path.exists(path):
                continue
            # most probably it is a git symlinked file

            # copy original content to filename
            shutil.copy(path, filename)
