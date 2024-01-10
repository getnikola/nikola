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

"""SoundCloud directive for reStructuredText."""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from nikola.plugins.compile.rest import _align_choice, _align_options_base

from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):
    """Plugin for soundclound directive."""

    name = "rest_soundcloud"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('soundcloud', SoundCloud)
        directives.register_directive('soundcloud_playlist', SoundCloudPlaylist)
        return super().set_site(site)


CODE = """\
<div class="soundcloud-player{align}">
<iframe width="{width}" height="{height}"
scrolling="no" frameborder="no"
src="https://w.soundcloud.com/player/?url=http://api.soundcloud.com/{preslug}/{sid}">
</iframe>
</div>"""


class SoundCloud(Directive):
    """reST extension for inserting SoundCloud embedded music.

    Usage:
        .. soundcloud:: <sound id>
           :height: 400
           :width: 600

    """

    has_content = True
    required_arguments = 1
    option_spec = {
        'width': directives.positive_int,
        'height': directives.positive_int,
        "align": _align_choice
    }
    preslug = "tracks"

    def run(self):
        """Run the soundcloud directive."""
        self.check_content()
        options = {
            'sid': self.arguments[0],
            'width': 600,
            'height': 160,
            'preslug': self.preslug,
        }
        options.update(self.options)
        if self.options.get('align') in _align_options_base:
            options['align'] = ' align-' + self.options['align']
        else:
            options['align'] = ''
        return [nodes.raw('', CODE.format(**options), format='html')]

    def check_content(self):
        """Emit a deprecation warning if there is content."""
        if self.content:  # pragma: no cover
            raise self.warning("This directive does not accept content. The "
                               "'key=value' format for options is deprecated, "
                               "use ':key: value' instead")


class SoundCloudPlaylist(SoundCloud):
    """reST directive for SoundCloud playlists."""

    preslug = "playlists"
