# -*- coding: utf-8 -*-

# Copyright © 2014-2015 Pelle Nilsson and others.

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

import os

from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image, Figure

from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):

    name = "rest_thumbnail"

    def set_site(self, site):
        self.site = site
        directives.register_directive('thumbnail', Thumbnail)
        return super(Plugin, self).set_site(site)


class Thumbnail(Figure):

    def align(argument):
        return directives.choice(argument, Image.align_values)

    def figwidth_value(argument):
        if argument.lower() == 'image':
            return 'image'
        else:
            return directives.length_or_percentage_or_unitless(argument, 'px')

    option_spec = Image.option_spec.copy()
    option_spec['figwidth'] = figwidth_value
    option_spec['figclass'] = directives.class_option
    has_content = True

    def run(self):
        uri = directives.uri(self.arguments[0])
        self.options['target'] = uri
        self.arguments[0] = '.thumbnail'.join(os.path.splitext(uri))
        if self.content:
            (node,) = Figure.run(self)
        else:
            (node,) = Image.run(self)
        return [node]
