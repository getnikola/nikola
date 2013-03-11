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

from __future__ import unicode_literals

import codecs
import os

try:
    from markdown import markdown

    from nikola.plugins.compile_markdown.mdx_nikola import NikolaExtension
    nikola_extension = NikolaExtension()

    from nikola.plugins.compile_markdown.mdx_gist import GistExtension
    gist_extension = GistExtension()

    from nikola.plugins.compile_markdown.mdx_podcast import PodcastExtension
    podcast_extension = PodcastExtension()

except ImportError:
    markdown = None  # NOQA
    nikola_extension = None
    gist_extension = None

from nikola.plugin_categories import PageCompiler


class CompileMarkdown(PageCompiler):
    """Compile markdown into HTML."""

    name = "markdown"

    extensions = ['fenced_code', 'codehilite', gist_extension,
                  nikola_extension, podcast_extension]

    def compile_html(self, source, dest):
        if markdown is None:
            raise Exception('To build this site, you need to install the '
                            '"markdown" package.')
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
            output = markdown(data, self.extensions)
            out_file.write(output)

    def create_post(self, path, onefile=False, title="", slug="", date="",
                    tags=""):
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
            fd.write("\nWrite your post here.")
