# -*- coding: utf-8 -*-

# Copyright © 2012-2019 Roberto Alsina and others.

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

"""SlideShare directive for reStructuredText."""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from nikola.plugins.compile.rest import _align_choice, _align_options_base

from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):
    """Plugin for the ``slideshare`` directive."""

    name = "rest_slideshare"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('slideshare', SlideShare)
        return super(Plugin, self).set_site(site)


CODE = '<iframe src="https://www.slideshare.net/slideshow/embed_code/key/{key}" width="{width}" height="{height}" ' \
       'frameborder="0" marginwidth="0" marginheight="0" scrolling="no" ' \
       'style="border:1px solid #CCC; border-width:1px; margin-bottom:5px; max-width: 100%;" ' \
       'allowfullscreen></iframe>'


class SlideShare(Directive):
    """reST extension for inserting SlideShare embedded slides.

    Usage:
        .. slideshare:: hIdRKXzzqZsgyR
           :height: 595
           :width: 485

    """

    has_content = True
    required_arguments = 1
    option_spec = {
        "width": directives.unchanged,
        "height": directives.unchanged,
    }

    _DEFAULT_HEIGHT = 485
    _DEFAULT_WIDTH = 595

    def run(self):
        """Run the slideshare directive."""
        self.check_content()
        options = {
            'key': self.arguments[0],
            'width': SlideShare._DEFAULT_WIDTH,
            'height': SlideShare._DEFAULT_HEIGHT,
        }
        options.update({k: v for k, v in self.options.items() if v})
        return [nodes.raw('', CODE.format(**options), format='html')]

    def check_content(self):
        """Check if content exists."""
        if self.content:  # pragma: no cover
            raise self.warning("This directive does not accept content. The "
                               "'key=value' format for options is deprecated, "
                               "use ':key: value' instead")
