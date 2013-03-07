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

import os
import shutil
import codecs

from nikola.plugin_categories import PageCompiler


class CompileHtml(PageCompiler):
    """Compile HTML into HTML."""

    name = "html"

    def compile_html(self, source, dest):
        try:
            os.makedirs(os.path.dirname(dest))
        except Exception:
            pass
        shutil.copyfile(source, dest)

    def create_post(self, path, onefile=False, title="", slug="",
                    date="", tags=""):
        d_name = os.path.dirname(path)
        if not os.path.isdir(d_name):
            os.makedirs(os.path.dirname(path))
        with codecs.open(path, "wb+", "utf8") as fd:
            if onefile:
                fd.write('<!-- \n')
                fd.write('.. title: {0}\n'.format(title))
                fd.write('.. slug: {0}\n'.format(slug))
                fd.write('.. date: {0}\n'.format(date))
                fd.write('.. tags: {0}\n'.format(tags))
                fd.write('.. link: \n')
                fd.write('.. description: \n')
                fd.write('-->\n\n')
            fd.write("\n<p>Write your post here.</p>")
