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


"""Define and register a listing directive using the existing CodeBlock."""


import io
import os
import uuid
from urllib.parse import urlunsplit

import docutils.parsers.rst.directives.body
import docutils.parsers.rst.directives.misc
import pygments
import pygments.util
from docutils import core
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.directives.misc import Include
from pygments.lexers import get_lexer_by_name

from nikola import utils
from nikola.plugin_categories import RestExtension


# A sanitized version of docutils.parsers.rst.directives.body.CodeBlock.
class CodeBlock(Directive):
    """Parse and mark up content of a code block."""

    optional_arguments = 1
    option_spec = {'class': directives.class_option,
                   'name': directives.unchanged,
                   'number-lines': directives.unchanged,  # integer or None
                   'linenos': directives.unchanged,
                   'tab-width': directives.nonnegative_int,
                   'emphasize-lines': directives.unchanged_required}
    has_content = True

    def run(self):
        """Run code block directive."""
        self.assert_has_content()

        if 'linenos' in self.options:
            self.options['number-lines'] = self.options['linenos']
        if 'tab-width' in self.options:
            self.content = [x.replace('\t', ' ' * self.options['tab-width']) for x in self.content]

        if self.arguments:
            language = self.arguments[0]
        else:
            language = 'text'
        set_classes(self.options)
        classes = ['code']
        if language:
            classes.append(language)
        if 'classes' in self.options:
            classes.extend(self.options['classes'])

        code = '\n'.join(self.content)

        try:
            lexer = get_lexer_by_name(language)
        except pygments.util.ClassNotFound:
            raise self.error('Cannot find pygments lexer for language "{0}"'.format(language))

        if 'number-lines' in self.options:
            linenos = 'table'
            # optional argument `startline`, defaults to 1
            try:
                linenostart = int(self.options['number-lines'] or 1)
            except ValueError:
                raise self.error(':number-lines: with non-integer start value')
        else:
            linenos = False
            linenostart = 1  # actually unused

        if self.site.invariant:  # for testing purposes
            anchor_ref = 'rest_code_' + 'fixedvaluethatisnotauuid'
        else:
            anchor_ref = 'rest_code_' + uuid.uuid4().hex

        linespec = self.options.get('emphasize-lines')
        if linespec:
            try:
                nlines = len(self.content)
                hl_lines = utils.parselinenos(linespec, nlines)
                if any(i >= nlines for i in hl_lines):
                    raise self.error(
                        'line number spec is out of range(1-%d): %r' %
                        (nlines, self.options['emphasize-lines'])
                    )
                hl_lines = [x + 1 for x in hl_lines if x < nlines]
            except ValueError as err:
                raise self.error(err)
        else:
            hl_lines = None

        extra_kwargs = {}
        if hl_lines is not None:
            extra_kwargs['hl_lines'] = hl_lines

        formatter = utils.NikolaPygmentsHTML(
            anchor_ref=anchor_ref,
            classes=classes,
            linenos=linenos,
            linenostart=linenostart,
            **extra_kwargs
        )
        out = pygments.highlight(code, lexer, formatter)
        node = nodes.raw('', out, format='html')

        self.add_name(node)
        # if called from "include", set the source
        if 'source' in self.options:
            node.attributes['source'] = self.options['source']

        return [node]


# Monkey-patch: replace insane docutils CodeBlock with our implementation.
docutils.parsers.rst.directives.body.CodeBlock = CodeBlock
docutils.parsers.rst.directives.misc.CodeBlock = CodeBlock


class Plugin(RestExtension):
    """Plugin for listing directive."""

    name = "rest_listing"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        # Even though listings don't use CodeBlock anymore, I am
        # leaving these to make the code directive work with
        # docutils < 0.9
        CodeBlock.site = site
        Listing.site = site
        directives.register_directive('code', CodeBlock)
        directives.register_directive('code-block', CodeBlock)
        directives.register_directive('sourcecode', CodeBlock)
        directives.register_directive('listing', Listing)
        Listing.folders = site.config['LISTINGS_FOLDERS']
        return super().set_site(site)


# Add sphinx compatibility option
listing_spec = Include.option_spec
listing_spec['linenos'] = directives.unchanged


class Listing(Include):
    """Create a highlighted block of code from a file in listings/.

    Usage:

        .. listing:: nikola.py python
           :number-lines:

    """

    has_content = False
    required_arguments = 1
    optional_arguments = 1
    option_spec = listing_spec

    def run(self):
        """Run listing directive."""
        _fname = self.arguments.pop(0)
        fname = _fname.replace('/', os.sep)
        try:
            lang = self.arguments.pop(0)
            self.options['code'] = lang
        except IndexError:
            self.options['literal'] = True

        if len(self.folders) == 1:
            listings_folder = next(iter(self.folders.keys()))
            if fname.startswith(listings_folder):
                fpath = os.path.join(fname)  # new syntax: specify folder name
            else:
                fpath = os.path.join(listings_folder, fname)  # old syntax: don't specify folder name
        else:
            fpath = os.path.join(fname)  # must be new syntax: specify folder name
        self.arguments.insert(0, fpath)
        if 'linenos' in self.options:
            self.options['number-lines'] = self.options['linenos']
        with io.open(fpath, 'r+', encoding='utf-8-sig') as fileobject:
            self.content = fileobject.read().splitlines()
        self.state.document.settings.record_dependencies.add(fpath)
        target = urlunsplit(("link", 'listing', fpath.replace('\\', '/'), '', ''))
        src_target = urlunsplit(("link", 'listing_source', fpath.replace('\\', '/'), '', ''))
        src_label = self.site.MESSAGES('Source')
        generated_nodes = (
            [core.publish_doctree('`{0} <{1}>`_  `({2}) <{3}>`_' .format(
                _fname, target, src_label, src_target))[0]])
        generated_nodes += self.get_code_from_file(fileobject)
        return generated_nodes

    def get_code_from_file(self, data):
        """Create CodeBlock nodes from file object content."""
        return super().run()

    def assert_has_content(self):
        """Override check from superclass with nothing.

        Listing has no content, override check from superclass.
        """
        pass
