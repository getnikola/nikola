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

"""Implementation of compile_html based on markdown."""

from __future__ import unicode_literals

import codecs
import os
import re

try:
    from markdown import markdown

    from nikola.plugins.compile.markdown.mdx_nikola import NikolaExtension
    nikola_extension = NikolaExtension()

    from nikola.plugins.compile.markdown.mdx_gist import GistExtension
    gist_extension = GistExtension()

    from nikola.plugins.compile.markdown.mdx_podcast import PodcastExtension
    podcast_extension = PodcastExtension()

except ImportError:
    markdown = None  # NOQA
    nikola_extension = None
    gist_extension = None
    podcast_extension = None


try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = None  # NOQA

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing


class CompileMarkdown(PageCompiler):
    """Compile markdown into HTML."""

    name = "markdown"
    demote_headers = True
    extensions = [gist_extension, nikola_extension, podcast_extension]
    site = None

    def compile_html(self, source, dest, is_two_file=True):
        if markdown is None:
            req_missing(['markdown'], 'build this site (compile Markdown)')
        makedirs(os.path.dirname(dest))
        self.extensions += self.site.config.get("MARKDOWN_EXTENSIONS")
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
            if not is_two_file:
                data = re.split('(\n\n|\r\n\r\n)', data, maxsplit=1)[-1]
            output = markdown(data, self.extensions)
            out_file.write(output)

    def create_post(self, path, onefile=False, **kw):
        if OrderedDict is not None:
            metadata = OrderedDict()
        else:
            metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)
        makedirs(os.path.dirname(path))
        with codecs.open(path, "wb+", "utf8") as fd:
            if onefile:
                fd.write('<!-- \n')
                for k, v in metadata.items():
                    fd.write('.. {0}: {1}\n'.format(k, v))
                fd.write('-->\n\n')
            fd.write("Write your post here.")
