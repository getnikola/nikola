# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Vimeo directive for reStructuredText."""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from nikola.plugins.compile.rest import _align_choice, _align_options_base

import requests
import json


from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):
    """Plugin for vimeo reST directive."""

    name = "rest_vimeo"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('vimeo', Vimeo)
        return super(Plugin, self).set_site(site)


CODE = """<div class="vimeo-video{align}">
<iframe src="https://player.vimeo.com/video/{vimeo_id}"
width="{width}" height="{height}"
frameborder="0" webkitAllowFullScreen="webkitAllowFullScreen" mozallowfullscreen="mozallowfullscreen" allowFullScreen="allowFullScreen">
</iframe>
</div>
"""

VIDEO_DEFAULT_HEIGHT = 500
VIDEO_DEFAULT_WIDTH = 281


class Vimeo(Directive):
    """reST extension for inserting vimeo embedded videos.

    Usage:
        .. vimeo:: 20241459
           :height: 400
           :width: 600

    """

    has_content = True
    required_arguments = 1
    option_spec = {
        "width": directives.positive_int,
        "height": directives.positive_int,
        "align": _align_choice
    }

    # set to False for not querying the vimeo api for size
    request_size = True

    def run(self):
        """Run the vimeo directive."""
        self.check_content()
        options = {
            'vimeo_id': self.arguments[0],
            'width': VIDEO_DEFAULT_WIDTH,
            'height': VIDEO_DEFAULT_HEIGHT,
        }
        if self.request_size:
            err = self.check_modules()
            if err:
                return err
            self.set_video_size()
        options.update(self.options)
        if self.options.get('align') in _align_options_base:
            options['align'] = ' align-' + self.options['align']
        else:
            options['align'] = ''
        return [nodes.raw('', CODE.format(**options), format='html')]

    def check_modules(self):
        """Check modules."""
        return None

    def set_video_size(self):
        """Set video size."""
        # Only need to make a connection if width and height aren't provided
        if 'height' not in self.options or 'width' not in self.options:
            self.options['height'] = VIDEO_DEFAULT_HEIGHT
            self.options['width'] = VIDEO_DEFAULT_WIDTH

            if json:  # we can attempt to retrieve video attributes from vimeo
                try:
                    url = ('https://vimeo.com/api/v2/video/{0}'
                           '.json'.format(self.arguments[0]))
                    data = requests.get(url).text
                    video_attributes = json.loads(data)[0]
                    self.options['height'] = video_attributes['height']
                    self.options['width'] = video_attributes['width']
                except Exception:
                    # fall back to the defaults
                    pass

    def check_content(self):
        """Check if content exists."""
        if self.content:
            raise self.warning("This directive does not accept content. The "
                               "'key=value' format for options is deprecated, "
                               "use ':key: value' instead")
