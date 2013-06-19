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


class CompileTextile(PageCompiler):
    """Compile textile into HTML."""

    name = "wiki"

    def compile_html(self, source, dest, is_two_file=True):
        if creole is None:
            raise Exception('To build this site, you need to install the '
                            '"creole" package.')
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
                document = Parser(data).parse()
            output = HtmlEmitter(document).emit()
            out_file.write(output)

    def create_post(self, path, onefile=False, **kw):
        metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)
        d_name = os.path.dirname(path)
        if not os.path.isdir(d_name):
            os.makedirs(os.path.dirname(path))
        if onefile:
            raise Exception('There are no comments in CreoleWiki markup, so '
                            'one-file format is not possible, use the -2 '
                            'option.')
        with codecs.open(path, "wb+", "utf8") as fd:
            fd.write("Write your post here.")
