"""Implementation of compile_html based on reStructuredText and docutils."""

__all__ = ['compile_html']

import codecs
import os

########################################
# custom rst directives and renderer
########################################
import docutils.core
import docutils.io
from docutils.parsers.rst import directives

from pygments_code_block_directive import code_block_directive, listings_directive
directives.register_directive('code-block', code_block_directive)
directives.register_directive('listing', listings_directive)

from youtube import youtube
directives.register_directive('youtube',youtube)

def compile_html(source, dest):
    try:
        os.makedirs(os.path.dirname(dest))
    except:
        pass
    error_level = 100
    with codecs.open(dest, "w+", "utf8") as out_file:
        with codecs.open(source, "r", "utf8") as in_file:
            data = in_file.read()
            output, error_level = rst2html(data,
                settings_overrides={'initial_header_level': 2})
            out_file.write(output)
    if error_level < 3:
        return True
    else:
        return False


def rst2html(source, source_path=None, source_class=docutils.io.StringInput,
                  destination_path=None,
                  reader=None, reader_name='standalone',
                  parser=None, parser_name='restructuredtext',
                  writer=None, writer_name='html',
                  settings=None, settings_spec=None,
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
