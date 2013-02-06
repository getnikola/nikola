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
from docutils.parsers.rst import directives

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

CODE = """<iframe src="http://player.vimeo.com/video/%(vimeo_id)s"
width="%(width)s" height="%(height)s"
frameborder="0" webkitAllowFullScreen mozallowfullscreen allowFullScreen>
</iframe>
"""

VIDEO_DEFAULT_HEIGHT = 500
VIDEO_DEFAULT_WIDTH = 281


def vimeo(name, args, options, content, lineno, contentOffset, blockText,
          state, stateMachine):
    """ Restructured text extension for inserting vimeo embedded videos """
    if requests is None:
        raise Exception("To use the Vimeo directive you need to install the "
                        "requests module.")
    if json is None:
        raise Exception("To use the Vimeo directive you need python 2.6 or to "
                        "install the simplejson module.")
    if len(content) == 0:
        return

    string_vars = {'vimeo_id': content[0]}
    extra_args = content[1:]  # Because content[0] is ID
    extra_args = [ea.strip().split("=") for ea in extra_args]  # key=value
    extra_args = [ea for ea in extra_args if len(ea) == 2]  # drop bad lines
    extra_args = dict(extra_args)
    if 'width' in extra_args:
        string_vars['width'] = extra_args.pop('width')
    if 'height' in extra_args:
        string_vars['height'] = extra_args.pop('height')

    # Only need to make a connection if width and height aren't provided
    if 'height' not in string_vars or 'width' not in string_vars:
        string_vars['height'] = VIDEO_DEFAULT_HEIGHT
        string_vars['width'] = VIDEO_DEFAULT_WIDTH

        if json:  # we can attempt to retrieve video attributes from vimeo
            try:
                url = ('http://vimeo.com/api/v2/video/%(vimeo_id)s.json' %
                       string_vars)
                data = requests.get(url).text
                video_attributes = json.loads(data)
                string_vars['height'] = video_attributes['height']
                string_vars['width'] = video_attributes['width']
            except Exception:
                # fall back to the defaults
                pass

    return [nodes.raw('', CODE % string_vars, format='html')]

vimeo.content = True
directives.register_directive('vimeo', vimeo)
