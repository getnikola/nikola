# -*- coding: utf-8 -*-

# Copyright © 2012-2013 Roberto Alsina and others.

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
import re

try:
    import docutils.core
    import docutils.nodes
    import docutils.utils
    import docutils.io
    import docutils.readers.standalone
    has_docutils = True
except ImportError:
    has_docutils = False

from nikola.plugin_categories import PageCompiler
from nikola.utils import get_logger, makedirs, req_missing


class CompileRest(PageCompiler):
    """Compile reSt into HTML."""

    name = "rest"
    demote_headers = True
    logger = None

    def compile_html(self, source, dest, is_two_file=True):
        """Compile reSt into HTML."""

        if not has_docutils:
            req_missing(['docutils'], 'build this site (compile reStructuredText)')
        makedirs(os.path.dirname(dest))
        error_level = 100
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
                add_ln = 0
                if not is_two_file:
                    spl = re.split('(\n\n|\r\n\r\n)', data, maxsplit=1)
                    data = spl[-1]
                    if len(spl) != 1:
                        # If errors occur, this will be added to the line
                        # number reported by docutils so the line number
                        # matches the actual line number (off by 7 with default
                        # metadata, could be more or less depending on the post
                        # author).
                        add_ln = len(spl[0].splitlines()) + 1

                output, error_level, deps = rst2html(
                    data, settings_overrides={
                        'initial_header_level': 1,
                        'record_dependencies': True,
                        'stylesheet_path': None,
                        'link_stylesheet': True,
                        'syntax_highlight': 'short',
                        'math_output': 'mathjax',
                    }, logger=self.logger, l_source=source, l_add_ln=add_ln)
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
        makedirs(os.path.dirname(path))
        with codecs.open(path, "wb+", "utf8") as fd:
            if onefile:
                for k, v in metadata.items():
                    fd.write('.. {0}: {1}\n'.format(k, v))
            fd.write("\nWrite your post here.")

    def set_site(self, site):
        for plugin_info in site.plugin_manager.getPluginsOfCategory("RestExtension"):
            if (plugin_info.name in site.config['DISABLED_PLUGINS']
                or (plugin_info.name in site.EXTRA_PLUGINS and
                    plugin_info.name not in site.config['ENABLED_EXTRAS'])):
                site.plugin_manager.removePluginFromCategory(plugin_info, "RestExtension")
                continue

            site.plugin_manager.activatePluginByName(plugin_info.name)
            plugin_info.plugin_object.set_site(site)
            plugin_info.plugin_object.short_help = plugin_info.description

        self.logger = get_logger('compile_rest', site.loghandlers)
        return super(CompileRest, self).set_site(site)


def get_observer(settings):
    """Return an observer for the docutils Reporter."""
    def observer(msg):
        """Report docutils/rest messages to a Nikola user.

        Error code mapping:

        +------+---------+------+----------+
        | dNUM |   dNAME | lNUM |    lNAME |    d = docutils, l = logbook
        +------+---------+------+----------+
        |    0 |   DEBUG |    1 |    DEBUG |
        |    1 |    INFO |    2 |     INFO |
        |    2 | WARNING |    4 |  WARNING |
        |    3 |   ERROR |    5 |    ERROR |
        |    4 |  SEVERE |    6 | CRITICAL |
        +------+---------+------+----------+
        """
        errormap = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6}
        text = docutils.nodes.Element.astext(msg)
        line = msg['line'] + settings['add_ln'] if 'line' in msg else 0
        out = '[{source}:{line}] {text}'.format(source=settings['source'], line=line, text=text)
        settings['logger'].log(errormap[msg['level']], out)

    return observer


class NikolaReader(docutils.readers.standalone.Reader):

    def new_document(self):
        """Create and return a new empty document tree (root node)."""
        document = docutils.utils.new_document(self.source.source_path, self.settings)
        document.reporter.stream = False
        document.reporter.attach_observer(get_observer(self.l_settings))
        return document


def rst2html(source, source_path=None, source_class=docutils.io.StringInput,
             destination_path=None, reader=None,
             parser=None, parser_name='restructuredtext', writer=None,
             writer_name='html', settings=None, settings_spec=None,
             settings_overrides=None, config_section=None,
             enable_exit_status=None, logger=None, l_source='', l_add_ln=0):
    """
    Set up & run a `Publisher`, and return a dictionary of document parts.
    Dictionary keys are the names of parts, and values are Unicode strings;
    encoding is up to the client.  For programmatic use with string I/O.

    For encoded string input, be sure to set the 'input_encoding' setting to
    the desired encoding.  Set it to 'unicode' for unencoded Unicode string
    input.  Here's how::

        publish_parts(..., settings_overrides={'input_encoding': 'unicode'})

    Parameters: see `publish_programmatically`.

    WARNING: `reader` should be None (or NikolaReader()) if you want Nikola to report
             reStructuredText syntax errors.
    """
    if reader is None:
        reader = NikolaReader()
        # For our custom logging, we have special needs and special settings we
        # specify here.
        # logger    a logger from Nikola
        # source   source filename (docutils gets a string)
        # add_ln   amount of metadata lines (see comment in compile_html above)
        reader.l_settings = {'logger': logger, 'source': l_source,
                             'add_ln': l_add_ln}

    pub = docutils.core.Publisher(reader, parser, writer, settings=settings,
                                  source_class=source_class,
                                  destination_class=docutils.io.StringOutput)
    pub.set_components(None, parser_name, writer_name)
    pub.process_programmatic_settings(
        settings_spec, settings_overrides, config_section)
    pub.set_source(source, source_path)
    pub.set_destination(None, destination_path)
    pub.publish(enable_exit_status=enable_exit_status)

    return pub.writer.parts['docinfo'] + pub.writer.parts['fragment'], pub.document.reporter.max_level, pub.settings.record_dependencies
