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

"""Implementation of compile_html based on markdown."""

import codecs
import os
import re

from markdown import markdown

from nikola.plugin_categories import PageCompiler


class CompileMarkdown(PageCompiler):
    """Compile markdown into HTML."""

    name = "markdown"

    def compile_html(self, source, dest):
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
            output = markdown(data, ['fenced_code', 'codehilite'])
            # remove the H1 because there is "title" h1.
            output = re.sub(r'<h1>.*</h1>', '', output)
            # python-markdown's highlighter uses the class 'codehilite' to wrap
            # code, # instead of the standard 'code'. None of the standard
            # pygments stylesheets use this class, so swap it to be 'code'
            output = re.sub(r'(<div[^>]+class="[^"]*)codehilite([^>]+)',
                            r'\1code\2', output)
            out_file.write(output)
