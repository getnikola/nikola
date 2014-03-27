# -*- coding: utf-8 -*-

# Copyright © 2013-2014 Chris Lee and others.

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

"""Implementation of compile_html based on misaka."""

from __future__ import unicode_literals

import codecs
import os
import re

try:
    import misaka
except ImportError:
    misaka = None  # NOQA
    nikola_extension = None
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict  # NOQA

    gist_extension = None
    podcast_extension = None

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing


class CompileMisaka(PageCompiler):
    """Compile Misaka into HTML."""

    name = "misaka"
    demote_headers = True

    def __init__(self, *args, **kwargs):
        super(CompileMisaka, self).__init__(*args, **kwargs)
        if misaka is not None:
            self.ext = misaka.EXT_FENCED_CODE | misaka.EXT_STRIKETHROUGH | \
                misaka.EXT_AUTOLINK | misaka.EXT_NO_INTRA_EMPHASIS

    def compile_html(self, source, dest, is_two_file=True):
        if misaka is None:
            req_missing(['misaka'], 'build this site (compile with misaka)')
        makedirs(os.path.dirname(dest))
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
            if not is_two_file:
                data = re.split('(\n\n|\r\n\r\n)', data, maxsplit=1)[-1]
            output = misaka.html(data, extensions=self.ext)
            out_file.write(output)

    def create_post(self, path, content, onefile=False, is_page=False, **kw):
        metadata = OrderedDict()
        metadata.update(self.default_metadata)
        metadata.update(kw)
        makedirs(os.path.dirname(path))
        if not content.endswith('\n'):
            content += '\n'
        with codecs.open(path, "wb+", "utf8") as fd:
            if onefile:
                fd.write('<!-- \n')
                for k, v in metadata.items():
                    fd.write('.. {0}: {1}\n'.format(k, v))
                fd.write('-->\n\n')
            fd.write(content)
