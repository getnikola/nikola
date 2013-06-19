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

try:
    import docutils.core
    import docutils.io
    from docutils.parsers.rst import directives

    from .listing import Listing, CodeBlock
    directives.register_directive('code-block', CodeBlock)
    directives.register_directive('sourcecode', CodeBlock)
    directives.register_directive('listing', Listing)
    from .youtube import Youtube
    directives.register_directive('youtube', Youtube)
    from .vimeo import Vimeo
    directives.register_directive('vimeo', Vimeo)
    from .slides import Slides
    directives.register_directive('slides', Slides)
    from .gist_directive import GitHubGist
    directives.register_directive('gist', GitHubGist)
    from .soundcloud import SoundCloud
    directives.register_directive('soundcloud', SoundCloud)
    has_docutils = True
except ImportError:
    has_docutils = False

from nikola.plugin_categories import PageCompiler


class CompileRest(PageCompiler):
    """Compile reSt into HTML."""

    name = "rest"

    def compile_html(self, source, dest, is_two_file=True):
        """Compile reSt into HTML."""
        if not has_docutils:
            raise Exception('To build this site, you need to install the '
                            '"docutils" package.')
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        error_level = 100
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
                if not is_two_file:
                    data = data.split('\n\n', 1)[-1]
                output, error_level, deps = rst2html(
                    data, settings_overrides={
                        'initial_header_level': 2,
                        'record_dependencies': True,
                        'stylesheet_path': None,
                        'link_stylesheet': True,
                        'syntax_highlight': 'short',
                    })
                out_file.write(output)
            deps_path = dest + '.dep'
            if deps.list:
                with codecs.open(deps_path, "wb+", "utf8") as deps_file:
                    deps_file.write('\n'.join(deps.list))
            else:
                if os.path.isfile(deps_path):
                    os.unlink(deps_path)
        if error_level < 3:
            return True
        else:
            return False

    def create_post(self, path, onefile=False, **kw):
        metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)
        d_name = os.path.dirname(path)
        if not os.path.isdir(d_name):
            os.makedirs(os.path.dirname(path))
        with codecs.open(path, "wb+", "utf8") as fd:
            if onefile:
                for k, v in metadata.items():
                    fd.write('.. {0}: {1}\n'.format(k, v))
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
    return pub.writer.parts['fragment'], pub.document.reporter.max_level, pub.settings.record_dependencies
