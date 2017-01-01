# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Slides directive for reStructuredText."""

from __future__ import unicode_literals

import uuid

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):
    """Plugin for reST slides directive."""

    name = "rest_slides"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('slides', Slides)
        Slides.site = site
        return super(Plugin, self).set_site(site)


class Slides(Directive):
    """reST extension for inserting slideshows."""

    has_content = True

    def run(self):
        """Run the slides directive."""
        if len(self.content) == 0:  # pragma: no cover
            return

        if self.site.invariant:  # for testing purposes
            carousel_id = 'slides_' + 'fixedvaluethatisnotauuid'
        else:
            carousel_id = 'slides_' + uuid.uuid4().hex

        output = self.site.template_system.render_template(
            'slides.tmpl',
            None,
            {
                'slides_content': self.content,
                'carousel_id': carousel_id,
            }
        )
        return [nodes.raw('', output, format='html')]


directives.register_directive('slides', Slides)
