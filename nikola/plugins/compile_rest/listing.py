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
from codecs import open as codecs_open  # for patching purposes
try:
    from urlparse import urlunsplit
except ImportError:
    from urllib.parse import urlunsplit  # NOQA

from docutils import core
from docutils.parsers.rst import directives
try:
    from docutils.parsers.rst.directives.body import CodeBlock
except ImportError:  # docutils < 0.9 (Debian Sid For The Loss)
    from dummy import CodeBlock  # NOQA

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

    option_spec = {
        'start-at': directives.unchanged,
        'end-at': directives.unchanged,
        'start-after': directives.unchanged,
        'end-before': directives.unchanged,
    }

    def run(self):
        fname = self.arguments.pop(0)
        with codecs_open(os.path.join('listings', fname), 'rb+', 'utf8') as fileobject:
            self.content = fileobject.read().splitlines()
        self.trim_content()
        target = urlunsplit(("link", 'listing', fname, '', ''))
        generated_nodes = (
            [core.publish_doctree('`{0} <{1}>`_'.format(fname, target))[0]])
        generated_nodes += self.get_code_from_file(fileobject)
        return generated_nodes

    def trim_content(self):
        """Cut the contents based in options."""
        start = 0
        end = len(self.content)
        if 'start-at' in self.options:
            for start, l in enumerate(self.content):
                if self.options['start-at'] in l:
                    break
            else:
                start = 0
        elif 'start-before' in self.options:
            for start, l in enumerate(self.content):
                if self.options['start-before'] in l:
                    if start > 0:
                        start -= 1
                    break
            else:
                start = 0
        if 'end-at' in self.options:
            for end, l in enumerate(self.content):
                if self.options['end-at'] in l:
                    break
            else:
                end = len(self.content)
        elif 'end-before' in self.options:
            for end, l in enumerate(self.content):
                if self.options['end-before'] in l:
                    end -= 1
                    break
            else:
                end = len(self.content)

        self.content = self.content[start:end]

    def get_code_from_file(self, data):
        """ Create CodeBlock nodes from file object content """
        return super(Listing, self).run()

    def assert_has_content(self):
        """ Listing has no content, override check from superclass """
        pass


directives.register_directive('listing', Listing)
