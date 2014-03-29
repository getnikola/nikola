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

"""Implementation of compile_html based on CreoleWiki."""

import codecs
import os

try:
    from creole import Parser
    from creole.html_emitter import HtmlEmitter
    creole = True
except ImportError:
    creole = None

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing


class CompileWiki(PageCompiler):
    """Compile CreoleWiki into HTML."""

    name = "wiki"
    demote_headers = True
    supports_onefile = False

    def compile_html(self, source, dest, is_two_file=True):
        if creole is None:
            req_missing(['creole'], 'build this site (compile CreoleWiki)')
        makedirs(os.path.dirname(dest))
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
                document = Parser(data).parse()
            output = HtmlEmitter(document).emit()
            out_file.write(output)

    def create_post(self, path, **kw):
        content = kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        # is_page is not used by create_post as of now.
        kw.pop('is_page', False)
        if onefile:
            raise Exception('The one-file format is not supported by this compiler.')
        if not content.endswith('\n'):
            content += '\n'
        with codecs.open(path, "wb+", "utf8") as fd:
            fd.write(content)
