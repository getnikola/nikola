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

from __future__ import print_function, unicode_literals
import os
import sys

try:
    from mincss.processor import Processor
except ImportError:
    Processor = None

from nikola.plugin_categories import Command
from nikola.utils import req_missing, get_logger, STDERR_HANDLER


class CommandMincss(Command):
    """Check the generated site."""
    name = "mincss"

    doc_usage = ""
    doc_purpose = "apply mincss to the generated site"

    logger = get_logger('mincss', STDERR_HANDLER)

    def _execute(self, options, args):
        """Apply mincss the generated site."""
        output_folder = self.site.config['OUTPUT_FOLDER']
        if Processor is None:
            req_missing(['mincss'], 'use the "mincss" command')
            return

        p = Processor(preserve_remote_urls=False)
        urls = []
        css_files = {}
        for root, dirs, files in os.walk(output_folder, followlinks=True):
            for f in files:
                url = os.path.join(root, f)
                if url.endswith('.css'):
                    fname = os.path.basename(url)
                    if fname in css_files:
                        self.logger.error("You have two CSS files with the same name and that confuses me.")
                        sys.exit(1)
                    css_files[fname] = url
                if not f.endswith('.html'):
                    continue
                urls.append(url)
        p.process(*urls)
        for inline in p.links:
            fname = os.path.basename(inline.href)
            with open(css_files[fname], 'wb+') as outf:
                outf.write(inline.after)
