# coding: utf8
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


from docutils import nodes
from docutils.parsers.rst import Directive, directives

try:
    import requests
except ImportError:
    requests = None  # NOQA
try:
    import json  # python 2.6 or higher
except ImportError:
    try:
        import simplejson as json  # NOQA
    except ImportError:
        json = None


CODE = """<iframe src="http://player.vimeo.com/video/{vimeo_id}"
width="{width}" height="{height}"
frameborder="0" webkitAllowFullScreen mozallowfullscreen allowFullScreen>
</iframe>
"""

VIDEO_DEFAULT_HEIGHT = 500
VIDEO_DEFAULT_WIDTH = 281


class Vimeo(Directive):
    """ Restructured text extension for inserting vimeo embedded videos

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
    }

    # set to False for not querying the vimeo api for size
    request_size = True

    def run(self):
        self.check_content()
        options = {
            'vimeo_id': self.arguments[0],
            'width': VIDEO_DEFAULT_WIDTH,
            'height': VIDEO_DEFAULT_HEIGHT,
        }
        if self.request_size:
            self.check_modules()
            self.set_video_size()
        options.update(self.options)
        return [nodes.raw('', CODE.format(**options), format='html')]

    def check_modules(self):
        if requests is None:
            raise Exception("To use the Vimeo directive you need to install "
                            "the requests module.")
        if json is None:
            raise Exception("To use the Vimeo directive you need python 2.6 "
                            "or to install the simplejson module.")

    def set_video_size(self):
        # Only need to make a connection if width and height aren't provided
        if 'height' not in self.options or 'width' not in self.options:
            self.options['height'] = VIDEO_DEFAULT_HEIGHT
            self.options['width'] = VIDEO_DEFAULT_WIDTH

            if json:  # we can attempt to retrieve video attributes from vimeo
                try:
                    url = ('http://vimeo.com/api/v2/video/{0}'
                           '.json'.format(self.arguments[0]))
                    data = requests.get(url).text
                    video_attributes = json.loads(data)[0]
                    self.options['height'] = video_attributes['height']
                    self.options['width'] = video_attributes['width']
                except Exception:
                    # fall back to the defaults
                    pass

    def check_content(self):
        if self.content:
            raise self.warning("This directive does not accept content. The "
                               "'key=value' format for options is deprecated, "
                               "use ':key: value' instead")


directives.register_directive('vimeo', Vimeo)
