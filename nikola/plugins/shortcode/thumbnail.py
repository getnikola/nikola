# -*- coding: utf-8 -*-

# Copyright © 2017 Roberto Alsina, Chris Warrick and others.

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

"""Thumbnail shortcode (equivalent to reST’s thumbnail directive)."""

from nikola.plugin_categories import ShortcodePlugin

import os.path


class ThumbnailShortcode(ShortcodePlugin):
    """Plugin for thumbnail directive."""

    name = "thumbnail"

    def handler(self, uri, alt=None, align=None, target=None, site=None, data=None, lang=None, post=None):
        """Create HTML for thumbnail."""
        if uri.endswith('.svg'):
            # the ? at the end makes docutil output an <img> instead of an object for the svg, which colorbox requires
            src = '.thumbnail'.join(os.path.splitext(uri)) + '?'
        else:
            src = '.thumbnail'.join(os.path.splitext(uri))

        output = '<a href="{0}" class="image-reference"><img src="{1}"'.format(uri, src)
        if alt:
            output += ' alt="{}"'.format(alt)
        if align and not data:
            output += ' class="align-{}"'.format(align)
        output += '></a>'

        if data and align:
            output = '<div class="figure align-{2}">{0}{1}</div>'.format(output, data, align)
        elif data:
            output = '<div class="figure">{0}{1}</div>'.format(output, data)


        return output, []
