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

"""Implementation of compile_html based on asciidoc.

You will need, of course, to install asciidoc

"""

import codecs
import os
import subprocess

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict  # NOQA


class CompileAsciiDoc(PageCompiler):
    """Compile asciidoc into HTML."""

    name = "asciidoc"
    demote_headers = True

    def compile_html(self, source, dest, is_two_file=True):
        makedirs(os.path.dirname(dest))
        try:
            subprocess.check_call(('asciidoc', '-f', 'html', '-s', '-o', dest, source))
        except OSError as e:
            if e.strreror == 'No such file or directory':
                req_missing(['asciidoc'], 'build this site (compile with asciidoc)', python=False)

    def create_post(self, path, content, onefile=False, is_page=False, **kw):
        metadata = OrderedDict()
        metadata.update(self.default_metadata)
        metadata.update(kw)
        makedirs(os.path.dirname(path))
        if not content.endswith('\n'):
            content += '\n'
        with codecs.open(path, "wb+", "utf8") as fd:
            if onefile:
                fd.write("/////////////////////////////////////////////\n")
                for k, v in metadata.items():
                    fd.write('.. {0}: {1}\n'.format(k, v))
                fd.write("/////////////////////////////////////////////\n")
            fd.write(content)
