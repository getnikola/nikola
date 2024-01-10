# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

import io
import logging
import os

import docutils.core
import docutils.nodes
import docutils.transforms
import docutils.utils
import docutils.io
import docutils.readers.standalone
import docutils.writers.html5_polyglot
import docutils.parsers.rst.directives
from docutils.parsers.rst import roles

from nikola.nikola import LEGAL_VALUES
from nikola.metadata_extractors import MetaCondition
from nikola.plugin_categories import PageCompiler
from nikola.utils import (
    makedirs,
    write_metadata,
    LocaleBorg,
    map_metadata
)


class CompileRest(PageCompiler):
    """Compile reStructuredText into HTML."""

    name = "rest"
    friendly_name = "reStructuredText"
    demote_headers = True
    logger = None
    supports_metadata = True
    metadata_conditions = [(MetaCondition.config_bool, "USE_REST_DOCINFO_METADATA")]

    def read_metadata(self, post, lang=None):
        """Read the metadata from a post, and return a metadata dict."""
        if lang is None:
            lang = LocaleBorg().current_lang
        source_path = post.translated_source_path(lang)

        # Silence reST errors, some of which are due to a different
        # environment. Real issues will be reported while compiling.
        null_logger = logging.getLogger('NULL')
        null_logger.setLevel(1000)
        with io.open(source_path, 'r', encoding='utf-8-sig') as inf:
            data = inf.read()
            _, _, _, document = rst2html(data, logger=null_logger, source_path=source_path, transforms=self.site.rst_transforms)
        meta = {}
        if 'title' in document:
            meta['title'] = document['title']
        for docinfo in document.findall(docutils.nodes.docinfo):
            for element in docinfo.children:
                if element.tagname == 'field':  # custom fields (e.g. summary)
                    name_elem, body_elem = element.children
                    name = name_elem.astext()
                    value = body_elem.astext()
                elif element.tagname == 'authors':  # author list
                    name = element.tagname
                    value = [element.astext() for element in element.children]
                else:  # standard fields (e.g. address)
                    name = element.tagname
                    value = element.astext()
                name = name.lower()

                meta[name] = value

        # Put 'authors' meta field contents in 'author', too
        if 'authors' in meta and 'author' not in meta:
            meta['author'] = '; '.join(meta['authors'])

        # Map metadata from other platforms to names Nikola expects (Issue #2817)
        map_metadata(meta, 'rest_docinfo', self.site.config)
        return meta

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile reST into HTML strings."""
        # If errors occur, this will be added to the line number reported by
        # docutils so the line number matches the actual line number (off by
        # 7 with default metadata, could be more or less depending on the post).
        add_ln = 0
        if not is_two_file:
            m_data, data = self.split_metadata(data, post, lang)
            add_ln = len(m_data.splitlines()) + 1

        default_template_path = os.path.join(os.path.dirname(__file__), 'template.txt')
        settings_overrides = {
            'initial_header_level': 1,
            'record_dependencies': True,
            'stylesheet_path': None,
            'link_stylesheet': True,
            'syntax_highlight': 'short',
            # This path is not used by Nikola, but we need something to silence
            # warnings about it from reST.
            'math_output': 'mathjax /assets/js/mathjax.js',
            'template': default_template_path,
            'language_code': LEGAL_VALUES['DOCUTILS_LOCALES'].get(LocaleBorg().current_lang, 'en'),
            'doctitle_xform': self.site.config.get('USE_REST_DOCINFO_METADATA'),
            'file_insertion_enabled': self.site.config.get('REST_FILE_INSERTION_ENABLED'),
        }

        from nikola import shortcodes as sc
        new_data, shortcodes = sc.extract_shortcodes(data)
        if self.site.config.get('HIDE_REST_DOCINFO', False):
            self.site.rst_transforms.append(RemoveDocinfo)
        output, error_level, deps, _ = rst2html(
            new_data, settings_overrides=settings_overrides, logger=self.logger, source_path=source_path, l_add_ln=add_ln, transforms=self.site.rst_transforms)
        if not isinstance(output, str):
            # To prevent some weird bugs here or there.
            # Original issue: empty files.  `output` became a bytestring.
            output = output.decode('utf-8')

        output, shortcode_deps = self.site.apply_shortcodes_uuid(output, shortcodes, filename=source_path, extra_context={'post': post})
        return output, error_level, deps, shortcode_deps

    def compile(self, source, dest, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        error_level = 100
        with io.open(dest, "w+", encoding="utf-8") as out_file:
            with io.open(source, "r", encoding="utf-8-sig") as in_file:
                data = in_file.read()
                output, error_level, deps, shortcode_deps = self.compile_string(data, source, is_two_file, post, lang)
                out_file.write(output)
            if post is None:
                if deps.list:
                    self.logger.error(
                        "Cannot save dependencies for post {0} (post unknown)",
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
        with io.open(path, "w+", encoding="utf-8") as fd:
            if onefile:
                fd.write(write_metadata(metadata, comment_wrap=False, site=self.site, compiler=self))
            fd.write(content)

    def set_site(self, site):
        """Set Nikola site."""
        super().set_site(site)
        self.config_dependencies = []
        for plugin_info in self.get_compiler_extensions():
            self.config_dependencies.append(plugin_info.name)
            plugin_info.plugin_object.short_help = plugin_info.description

        if not site.debug:
            self.logger.level = logging.WARNING


def get_observer(settings):
    """Return an observer for the docutils Reporter."""
    def observer(msg):
        """Report docutils/rest messages to a Nikola user.

        Error code mapping:

        +----------+----------+
        | docutils |  logging |
        +----------+----------+
        |    DEBUG |    DEBUG |
        |     INFO |     INFO |
        |  WARNING |  WARNING |
        |    ERROR |    ERROR |
        |   SEVERE | CRITICAL |
        +----------+----------+
        """
        errormap = {
            docutils.utils.Reporter.DEBUG_LEVEL: logging.DEBUG,
            docutils.utils.Reporter.INFO_LEVEL: logging.INFO,
            docutils.utils.Reporter.WARNING_LEVEL: logging.WARNING,
            docutils.utils.Reporter.ERROR_LEVEL: logging.ERROR,
            docutils.utils.Reporter.SEVERE_LEVEL: logging.CRITICAL
        }
        text = docutils.nodes.Element.astext(msg)
        line = msg['line'] + settings['add_ln'] if 'line' in msg else ''
        out = '[{source}{colon}{line}] {text}'.format(
            source=settings['source'], colon=(':' if line else ''),
            line=line, text=text)
        settings['logger'].log(errormap[msg['level']], out)

    return observer


class NikolaReader(docutils.readers.standalone.Reader):
    """Nikola-specific docutils reader."""

    config_section = 'nikola'

    def __init__(self, *args, **kwargs):
        """Initialize the reader."""
        self.transforms = kwargs.pop('transforms', [])
        self.logging_settings = kwargs.pop('nikola_logging_settings', {})
        docutils.readers.standalone.Reader.__init__(self, *args, **kwargs)

    def get_transforms(self):
        """Get docutils transforms."""
        return docutils.readers.standalone.Reader(self).get_transforms() + self.transforms

    def new_document(self):
        """Create and return a new empty document tree (root node)."""
        document = docutils.utils.new_document(self.source.source_path, self.settings)
        document.reporter.stream = False
        document.reporter.attach_observer(get_observer(self.logging_settings))
        return document


def shortcode_role(name, rawtext, text, lineno, inliner,
                   options={}, content=[]):
    """Return a shortcode role that passes through raw inline HTML."""
    return [docutils.nodes.raw('', text, format='html')], []


roles.register_canonical_role('raw-html', shortcode_role)
roles.register_canonical_role('html', shortcode_role)
roles.register_canonical_role('sc', shortcode_role)


def add_node(node, visit_function=None, depart_function=None):
    """Register a Docutils node class.

    This function is completely optional. It is a same concept as
    `Sphinx add_node function <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_node>`_.

    For example::

        class Plugin(RestExtension):

            name = "rest_math"

            def set_site(self, site):
                self.site = site
                directives.register_directive('math', MathDirective)
                add_node(MathBlock, visit_Math, depart_Math)
                return super().set_site(site)

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
        setattr(docutils.writers.html5_polyglot.HTMLTranslator, 'visit_' + node.__name__, visit_function)
    if depart_function:
        setattr(docutils.writers.html5_polyglot.HTMLTranslator, 'depart_' + node.__name__, depart_function)


# Output <code> for ``double backticks``. (Code and extra logic based on html4css1 translator)
def visit_literal(self, node):
    """Output <code> for double backticks."""
    # special case: "code" role
    classes = node.get('classes', [])
    if 'code' in classes:
        # filter 'code' from class arguments
        node['classes'] = [cls for cls in classes if cls != 'code']
        self.body.append(self.starttag(node, 'code', ''))
        return
    self.body.append(
        self.starttag(node, 'code', '', CLASS='docutils literal'))
    text = node.astext()
    for token in self.words_and_spaces.findall(text):
        if token.strip():
            # Protect text like "--an-option" and the regular expression
            # ``[+]?(\d+(\.\d*)?|\.\d+)`` from bad line wrapping
            if self.in_word_wrap_point.search(token):
                self.body.append('<span class="pre">%s</span>'
                                 % self.encode(token))
            else:
                self.body.append(self.encode(token))
        elif token in ('\n', ' '):
            # Allow breaks at whitespace:
            self.body.append(token)
        else:
            # Protect runs of multiple spaces; the last space can wrap:
            self.body.append('&nbsp;' * (len(token) - 1) + ' ')
    self.body.append('</code>')
    # Content already processed:
    raise docutils.nodes.SkipNode


setattr(docutils.writers.html5_polyglot.HTMLTranslator, 'visit_literal', visit_literal)


def rst2html(source, source_path=None, source_class=docutils.io.StringInput,
             destination_path=None, reader=None,
             parser=None, parser_name='restructuredtext', writer=None,
             writer_name='html5_polyglot', settings=None, settings_spec=None,
             settings_overrides=None, config_section='nikola',
             enable_exit_status=None, logger=None, l_add_ln=0, transforms=None):
    """Set up & run a ``Publisher``, and return a dictionary of document parts.

    Dictionary keys are the names of parts, and values are Unicode strings;
    encoding is up to the client.  For programmatic use with string I/O.

    For encoded string input, be sure to set the 'input_encoding' setting to
    the desired encoding.  Set it to 'unicode' for unencoded Unicode string
    input.  Here's how::

        publish_parts(..., settings_overrides={'input_encoding': 'unicode'})

    For a description of the parameters, see `publish_programmatically`.

    WARNING: `reader` should be None (or NikolaReader()) if you want Nikola to report
             reStructuredText syntax errors.
    """
    if reader is None:
        # For our custom logging, we have special needs and special settings we
        # specify here.
        # logger    a logger from Nikola
        # source   source filename (docutils gets a string)
        # add_ln   amount of metadata lines (see comment in CompileRest.compile above)
        reader = NikolaReader(transforms=transforms,
                              nikola_logging_settings={
                                  'logger': logger, 'source': source_path,
                                  'add_ln': l_add_ln
                              })

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

    return pub.writer.parts['docinfo'] + pub.writer.parts['fragment'], pub.document.reporter.max_level, pub.settings.record_dependencies, pub.document


# Alignment helpers for extensions
_align_options_base = ('left', 'center', 'right')


def _align_choice(argument):
    return docutils.parsers.rst.directives.choice(argument, _align_options_base + ("none", ""))


class RemoveDocinfo(docutils.transforms.Transform):
    """Remove docinfo nodes."""

    default_priority = 870

    def apply(self):
        """Remove docinfo nodes."""
        for node in self.document.traverse(docutils.nodes.docinfo):
            node.parent.remove(node)
