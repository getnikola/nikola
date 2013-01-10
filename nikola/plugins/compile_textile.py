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

"""Implementation of compile_html based on textile."""

import codecs
import os
import re

try:
    from textile import textile
except ImportError:
    textile = None

from nikola.plugin_categories import PageCompiler


class CompileTextile(PageCompiler):
    """Compile textile into HTML."""

    name = "textile"

    def compile_html(self, source, dest):
        if textile is None:
            raise Exception('To build this site, you need to install the "textile" package.')
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
            output = textile(data, head_offset=1)
            out_file.write(output)
