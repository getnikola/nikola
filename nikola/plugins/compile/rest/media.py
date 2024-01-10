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

"""Media directive for reStructuredText."""

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from nikola.plugin_categories import RestExtension
from nikola.utils import req_missing

try:
    import micawber
except ImportError:
    micawber = None


class Plugin(RestExtension):
    """Plugin for reST media directive."""

    name = "rest_media"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('media', Media)
        self.site.register_shortcode('media', _gen_media_embed)
        return super().set_site(site)


class Media(Directive):
    """reST extension for inserting any sort of media using micawber."""

    has_content = False
    required_arguments = 1
    optional_arguments = 999

    def run(self):
        """Run media directive."""
        html = _gen_media_embed(" ".join(self.arguments))
        return [nodes.raw('', html, format='html')]


def _gen_media_embed(url, *q, **kw):
    if micawber is None:
        msg = req_missing(['micawber'], 'use the media directive', optional=True)
        return '<div class="text-error">{0}</div>'.format(msg)
    providers = micawber.bootstrap_basic()
    return micawber.parse_text(url, providers)
