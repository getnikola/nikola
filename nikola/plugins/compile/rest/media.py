# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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


from docutils import nodes
from docutils.parsers.rst import Directive, directives

try:
    import micawber
except ImportError:
    micawber = None  # NOQA


from nikola.plugin_categories import RestExtension
from nikola.utils import req_missing


class Plugin(RestExtension):

    name = "rest_media"

    def set_site(self, site):
        self.site = site
        directives.register_directive('media', Media)
        return super(Plugin, self).set_site(site)


class Media(Directive):
    """ Restructured text extension for inserting any sort of media using micawber."""
    has_content = False
    required_arguments = 1
    optional_arguments = 999

    def run(self):
        if micawber is None:
            msg = req_missing(['micawber'], 'use the media directive', optional=True)
            return [nodes.raw('', '<div class="text-error">{0}</div>'.format(msg), format='html')]

        providers = micawber.bootstrap_basic()
        return [nodes.raw('', micawber.parse_text(" ".join(self.arguments), providers), format='html')]
