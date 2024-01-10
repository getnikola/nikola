# -*- coding: utf-8 -*-

# Copyright © 2017-2024 Roberto Alsina, Chris Warrick and others.

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

import os.path

from nikola.plugin_categories import ShortcodePlugin


class ThumbnailShortcode(ShortcodePlugin):
    """Plugin for thumbnail directive."""

    name = "thumbnail"

    def handler(self, uri, alt=None, align=None, linktitle=None, title=None, imgclass=None, figclass=None, site=None, data=None, lang=None, post=None):
        """Create HTML for thumbnail."""
        if uri.endswith('.svg'):
            # the ? at the end makes docutil output an <img> instead of an object for the svg, which lightboxes may require
            src = '.thumbnail'.join(os.path.splitext(uri)) + '?'
        else:
            src = '.thumbnail'.join(os.path.splitext(uri))

        if imgclass is None:
            imgclass = ''
        if figclass is None:
            figclass = ''

        if align and data:
            figclass += ' align-{0}'.format(align)
        elif align:
            imgclass += ' align-{0}'.format(align)

        output = '<a href="{0}" class="image-reference"'.format(uri)
        if linktitle:
            output += ' title="{0}"'.format(linktitle)
        output += '><img src="{0}"'.format(src)
        for item, name in ((alt, 'alt'), (title, 'title'), (imgclass, 'class')):
            if item:
                output += ' {0}="{1}"'.format(name, item)
        output += '></a>'

        if data:
            output = '<div class="figure {0}">{1}{2}</div>'.format(figclass, output, data)

        return output, []
