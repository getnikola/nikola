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

from __future__ import print_function, unicode_literals
import os
import sys

try:
    from mincss.processor import Processor
except ImportError:
    Processor = None

from nikola.plugin_categories import Command


class CommandMincss(Command):
    """Check the generated site."""

    name = "mincss"

    doc_usage = ""
    doc_purpose = "Apply mincss to the generated site."

    def _execute(self, options, args):
        """Apply mincss the generated site."""
        output_folder = self.site.config['OUTPUT_FOLDER']
        if Processor is None:
            print('To use the mincss command,'
                  ' you have to install the "mincss" package.')
            return

        p = Processor()
        urls = []
        css_files = {}
        for root, dirs, files in os.walk(output_folder):
            for f in files:
                url = os.path.join(root, f)
                if url.endswith('.css'):
                    fname = os.path.basename(url)
                    if fname in css_files:
                        print("You have two CSS files with the same name and that confuses me.")
                        sys.exit(1)
                    css_files[fname] = url
                if not f.endswith('.html'):
                    continue
                urls.append(url)
        p.process(*urls)
        for inline in p.links:
            fname = os.path.basename(inline.href)
            print("===>", inline.href, len(inline.before), len(inline.after))
            with open(css_files[fname], 'wb+') as outf:
                outf.write(inline.after)            
