# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""reStructuredText compiler for Nikola."""

from __future__ import unicode_literals
import io
import os

import docutils.core
import docutils.nodes
import docutils.utils
import docutils.io
import docutils.readers.standalone
import docutils.writers.html4css1
import docutils.parsers.rst.directives
from docutils.parsers.rst import roles

from nikola.nikola import LEGAL_VALUES
from nikola.plugin_categories import PageCompiler
from nikola.utils import (
    unicode_str,
    get_logger,
    makedirs,
    write_metadata,
    STDERR_HANDLER,
    LocaleBorg
)


class CompileRest(PageCompiler):
    """Compile reStructuredText into HTML."""

    name = "rest"
    friendly_name = "reStructuredText"
    demote_headers = True
    logger = None

    def compile_html_string(self, data, source_path=None, is_two_file=True):
        """Compile reST into HTML strings."""
        # If errors occur, this will be added to the line number reported by
        # docutils so the line number matches the actual line number (off by
        # 7 with default metadata, could be more or less depending on the post).
        add_ln = 0
        if not is_two_file:
            m_data, data = self.split_metadata(data)
            add_ln = len(m_data.splitlines()) + 1

        default_template_path = os.path.join(os.path.dirname(__file__), 'template.txt')
        settings_overrides = {
            'initial_header_level': 1,
            'record_dependencies': True,
            'stylesheet_path': None,
            'link_stylesheet': True,
            'syntax_highlight': 'short',
            'math_output': 'mathjax',
            'template': default_template_path,
            'language_code': LEGAL_VALUES['DOCUTILS_LOCALES'].get(LocaleBorg().current_lang, 'en')
        }

        output, error_level, deps = rst2html(
            data, settings_overrides=settings_overrides, logger=self.logger, source_path=source_path, l_add_ln=add_ln, transforms=self.site.rst_transforms,
            no_title_transform=self.site.config.get('NO_DOCUTILS_TITLE_TRANSFORM', False))
        if not isinstance(output, unicode_str):
            # To prevent some weird bugs here or there.
            # Original issue: empty files.  `output` became a bytestring.
            output = output.decode('utf-8')
        return output, error_level, deps

    def compile_html(self, source, dest, is_two_file=True):
        """Compile source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        error_level = 100
        with io.open(dest, "w+", encoding="utf8") as out_file:
            try:
                post = self.site.post_per_input_file[source]
            except KeyError:
                post = None
            with io.open(source, "r", encoding="utf8") as in_file:
                data = in_file.read()
                output, error_level, deps = self.compile_html_string(data, source, is_two_file)
                output, shortcode_deps = self.site.apply_shortcodes(output, filename=source, with_dependencies=True, extra_context=dict(post=post))
                out_file.write(output)
            if post is None:
                if deps.list:
                    self.logger.error(
                        "Cannot save dependencies for post {0} due to unregistered source file name",
                        source)
            else:
                post._depfile[dest] += deps.list
                post._depfile[dest] += shortcode_deps
        if error_level < 3:
            return True
        else:
            return False

    def create_post(self, path, **kw):
        """Create a new post."""
        content = kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        # is_page is not used by create_post as of now.
        kw.pop('is_page', False)
        metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)
        makedirs(os.path.dirname(path))
        if not content.endswith('\n'):
            content += '\n'
        with io.open(path, "w+", encoding="utf8") as fd:
            if onefile:
                fd.write(write_metadata(metadata))
                fd.write('\n')
            fd.write(content)

    def set_site(self, site):
        """Set Nikola site."""
        super(CompileRest, self).set_site(site)
        self.config_dependencies = []
        for plugin_info in self.get_compiler_extensions():
            self.config_dependencies.append(plugin_info.name)
            plugin_info.plugin_object.short_help = plugin_info.description

        self.logger = get_logger('compile_rest', STDERR_HANDLER)
        if not site.debug:
            self.logger.level = 4


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
        out = '[{source}{colon}{line}] {text}'.format(
            source=settings['source'], colon=(':' if line else ''),
            line=line, text=text)
        settings['logger'].log(errormap[msg['level']], out)

    return observer


class NikolaReader(docutils.readers.standalone.Reader):
    """Nikola-specific docutils reader."""

    def __init__(self, *args, **kwargs):
        """Initialize the reader."""
        self.transforms = kwargs.pop('transforms', [])
        self.no_title_transform = kwargs.pop('no_title_transform', False)
        docutils.readers.standalone.Reader.__init__(self, *args, **kwargs)

    def get_transforms(self):
        """Get docutils transforms."""
        transforms = docutils.readers.standalone.Reader(self).get_transforms() + self.transforms
        if self.no_title_transform:
            transforms = [t for t in transforms if str(t) != "<class 'docutils.transforms.frontmatter.DocTitle'>"]
        return transforms

    def new_document(self):
        """Create and return a new empty document tree (root node)."""
        document = docutils.utils.new_document(self.source.source_path, self.settings)
        document.reporter.stream = False
        document.reporter.attach_observer(get_observer(self.l_settings))
        return document


def shortcode_role(name, rawtext, text, lineno, inliner,
                   options={}, content=[]):
    """A shortcode role that passes through raw inline HTML."""
    return [docutils.nodes.raw('', text, format='html')], []

roles.register_canonical_role('raw-html', shortcode_role)
roles.register_canonical_role('html', shortcode_role)
roles.register_canonical_role('sc', shortcode_role)


def add_node(node, visit_function=None, depart_function=None):
    """Register a Docutils node class.

    This function is completely optional. It is a same concept as
    `Sphinx add_node function <http://sphinx-doc.org/extdev/appapi.html#sphinx.application.Sphinx.add_node>`_.

    For example::

        class Plugin(RestExtension):

            name = "rest_math"

            def set_site(self, site):
                self.site = site
                directives.register_directive('math', MathDirective)
                add_node(MathBlock, visit_Math, depart_Math)
                return super(Plugin, self).set_site(site)

        class MathDirective(Directive):
            def run(self):
                node = MathBlock()
                return [node]

        class Math(docutils.nodes.Element): pass

        def visit_Math(self, node):
            self.body.append(self.starttag(node, 'math'))

        def depart_Math(self, node):
            self.body.append('</math>')

    For full example, you can refer to `Microdata plugin <https://plugins.getnikola.com/#microdata>`_
    """
    docutils.nodes._add_node_class_names([node.__name__])
    if visit_function:
        setattr(docutils.writers.html4css1.HTMLTranslator, 'visit_' + node.__name__, visit_function)
    if depart_function:
        setattr(docutils.writers.html4css1.HTMLTranslator, 'depart_' + node.__name__, depart_function)


def rst2html(source, source_path=None, source_class=docutils.io.StringInput,
             destination_path=None, reader=None,
             parser=None, parser_name='restructuredtext', writer=None,
             writer_name='html', settings=None, settings_spec=None,
             settings_overrides=None, config_section=None,
             enable_exit_status=None, logger=None, l_add_ln=0, transforms=None,
             no_title_transform=False):
    """Set up & run a ``Publisher``, and return a dictionary of document parts.

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
        reader = NikolaReader(transforms=transforms, no_title_transform=no_title_transform)
        # For our custom logging, we have special needs and special settings we
        # specify here.
        # logger    a logger from Nikola
        # source   source filename (docutils gets a string)
        # add_ln   amount of metadata lines (see comment in compile_html above)
        reader.l_settings = {'logger': logger, 'source': source_path,
                             'add_ln': l_add_ln}

    pub = docutils.core.Publisher(reader, parser, writer, settings=settings,
                                  source_class=source_class,
                                  destination_class=docutils.io.StringOutput)
    pub.set_components(None, parser_name, writer_name)
    pub.process_programmatic_settings(
        settings_spec, settings_overrides, config_section)
    pub.set_source(source, None)
    pub.settings._nikola_source_path = source_path
    pub.set_destination(None, destination_path)
    pub.publish(enable_exit_status=enable_exit_status)

    return pub.writer.parts['docinfo'] + pub.writer.parts['fragment'], pub.document.reporter.max_level, pub.settings.record_dependencies

# Alignment helpers for extensions
_align_options_base = ('left', 'center', 'right')


def _align_choice(argument):
    return docutils.parsers.rst.directives.choice(argument, _align_options_base + ("none", ""))
