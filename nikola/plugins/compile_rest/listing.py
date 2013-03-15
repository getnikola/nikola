# -*- coding: utf-8 -*-
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


""" Define and register a listing directive using the existing CodeBlock """


from __future__ import unicode_literals

try:
    from urlparse import urlunsplit
except ImportError:
    from urllib.parse import urlunsplit  # NOQA

from docutils import core
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.body import CodeBlock

import os


class Listing(CodeBlock):
    """ listing directive: create a CodeBlock from file

    Usage:

        .. listing:: nikola.py python
           :number-lines:

    """
    has_content = False
    required_arguments = 1
    optional_arguments = 1
    open = open  # dependency injection for easy mocking

    def run(self):
        fname = self.arguments.pop(0)
        fileobject = self.open(os.path.join('listings', fname), 'r')
        target = urlunsplit(("link", 'listing', fname, '', ''))
        generated_nodes = (
            [core.publish_doctree('`{0} <{1}>`_'.format(fname, target))[0]])
        generated_nodes += self.get_code_from_file(fileobject)
        return generated_nodes

    def get_code_from_file(self, fileobject):
        """ Create CodeBlock nodes from file object content """
        self.content = fileobject.read().splitlines()
        return super(Listing, self).run()

    def assert_has_content(self):
        """ Listing has no content, override check from superclass """
        pass


directives.register_directive('listing', Listing)
