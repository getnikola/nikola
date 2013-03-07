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

from __future__ import unicode_literals
import codecs
import os

import docutils.core
import docutils.io
from docutils.parsers.rst import directives

from .pygments_code_block_directive import (
    code_block_directive,
    listings_directive)
directives.register_directive('code-block', code_block_directive)
directives.register_directive('listing', listings_directive)

from .youtube import youtube
directives.register_directive('youtube', youtube)
from .vimeo import vimeo
directives.register_directive('vimeo', vimeo)
from .slides import slides
directives.register_directive('slides', slides)
from .gist_directive import GitHubGist
directives.register_directive('gist', GitHubGist)
from .soundcloud import soundcloud
directives.register_directive('soundcloud', soundcloud)

from nikola.plugin_categories import PageCompiler


class CompileRest(PageCompiler):
    """Compile reSt into HTML."""

    name = "rest"

    def compile_html(self, source, dest):
        """Compile reSt into HTML."""
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        error_level = 100
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
                output, error_level = rst2html(
                    data, settings_overrides={'initial_header_level': 2})
                out_file.write(output)
        if error_level < 3:
            return True
        else:
            return False

    def create_post(self, path, onefile=False, title="", slug="", date="",
                    tags=""):
        with codecs.open(path, "wb+", "utf8") as fd:
            if onefile:
                fd.write('.. title: {0}\n'.format(title))
                fd.write('.. slug: {0}\n'.format(slug))
                fd.write('.. date: {0}\n'.format(date))
                fd.write('.. tags: {0}\n'.format(tags))
                fd.write('.. link: \n')
                fd.write('.. description: \n\n')
            fd.write("\nWrite your post here.")


def rst2html(source, source_path=None, source_class=docutils.io.StringInput,
             destination_path=None, reader=None, reader_name='standalone',
             parser=None, parser_name='restructuredtext', writer=None,
             writer_name='html', settings=None, settings_spec=None,
             settings_overrides=None, config_section=None,
             enable_exit_status=None):
    """
    Set up & run a `Publisher`, and return a dictionary of document parts.
    Dictionary keys are the names of parts, and values are Unicode strings;
    encoding is up to the client.  For programmatic use with string I/O.

    For encoded string input, be sure to set the 'input_encoding' setting to
    the desired encoding.  Set it to 'unicode' for unencoded Unicode string
    input.  Here's how::

        publish_parts(..., settings_overrides={'input_encoding': 'unicode'})

    Parameters: see `publish_programmatically`.
    """
    output, pub = docutils.core.publish_programmatically(
        source=source, source_path=source_path, source_class=source_class,
        destination_class=docutils.io.StringOutput,
        destination=None, destination_path=destination_path,
        reader=reader, reader_name=reader_name,
        parser=parser, parser_name=parser_name,
        writer=writer, writer_name=writer_name,
        settings=settings, settings_spec=settings_spec,
        settings_overrides=settings_overrides,
        config_section=config_section,
        enable_exit_status=enable_exit_status)
    return pub.writer.parts['fragment'], pub.document.reporter.max_level
