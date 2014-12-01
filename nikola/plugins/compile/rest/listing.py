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


""" Define and register a listing directive using the existing CodeBlock """


from __future__ import unicode_literals
import io
import os
try:
    from urlparse import urlunsplit
except ImportError:
    from urllib.parse import urlunsplit  # NOQA

from docutils import core
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives.misc import Include
try:
    from docutils.parsers.rst.directives.body import CodeBlock
except ImportError:  # docutils < 0.9 (Debian Sid For The Loss)
    class CodeBlock(Directive):
        required_arguments = 1
        has_content = True
        option_spec = {}
        CODE = '<pre>{0}</pre>'

        def run(self):
            """ Required by the Directive interface. Create docutils nodes """
            return [nodes.raw('', self.CODE.format('\n'.join(self.content)), format='html')]
    directives.register_directive('code', CodeBlock)


from nikola.plugin_categories import RestExtension

# Add sphinx compatibility option
CodeBlock.option_spec['linenos'] = directives.unchanged


class FlexibleCodeBlock(CodeBlock):
    def run(self):
        if 'linenos' in self.options:
            self.options['number-lines'] = self.options['linenos']
        if 'tab-width' in self.options:
            self.content = self.content.replace('\t', ' ' * self.options['tab-width'])

        return super(FlexibleCodeBlock, self).run()
CodeBlock = FlexibleCodeBlock
# Add useful stuff to code directive
cb_spec = CodeBlock.option_spec
cb_spec['tab-width'] = directives.nonnegative_int


class Plugin(RestExtension):

    name = "rest_listing"

    def set_site(self, site):
        self.site = site
        # Even though listings don't use CodeBlock anymore, I am
        # leaving these to make the code directive work with
        # docutils < 0.9
        directives.register_directive('code', CodeBlock)
        directives.register_directive('code-block', CodeBlock)
        directives.register_directive('sourcecode', CodeBlock)
        directives.register_directive('listing', Listing)
        Listing.folders = site.config['LISTINGS_FOLDERS']
        return super(Plugin, self).set_site(site)


# Add sphinx compatibility option
listing_spec = Include.option_spec
listing_spec['linenos'] = directives.unchanged


class Listing(Include):
    """ listing directive: create a highlighted block of code from a file in listings/

    Usage:

        .. listing:: nikola.py python
           :number-lines:

    """
    has_content = False
    required_arguments = 1
    optional_arguments = 1
    option_spec = listing_spec

    def run(self):
        fname = self.arguments.pop(0)
        lang = self.arguments.pop(0)
        if len(self.folders) == 1:
            listings_folder = next(iter(self.folders.keys()))
            if fname.startswith(listings_folder):
                fpath = os.path.join(fname)  # new syntax: specify folder name
            else:
                fpath = os.path.join(listings_folder, fname)  # old syntax: don't specify folder name
        else:
            fpath = os.path.join(fname)  # must be new syntax: specify folder name
        self.arguments.insert(0, fpath)
        self.options['code'] = lang
        if 'linenos' in self.options:
            self.options['number-lines'] = self.options['linenos']
        with io.open(fpath, 'r+', encoding='utf8') as fileobject:
            self.content = fileobject.read().splitlines()
        self.state.document.settings.record_dependencies.add(fpath)
        target = urlunsplit(("link", 'listing', fpath, '', ''))
        generated_nodes = (
            [core.publish_doctree('`{0} <{1}>`_'.format(fname, target))[0]])
        generated_nodes += self.get_code_from_file(fileobject)
        return generated_nodes

    def get_code_from_file(self, data):
        """ Create CodeBlock nodes from file object content """
        return super(Listing, self).run()

    def assert_has_content(self):
        """ Listing has no content, override check from superclass """
        pass
