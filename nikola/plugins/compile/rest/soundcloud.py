# -*- coding: utf-8 -*-


from docutils import nodes
from docutils.parsers.rst import Directive, directives


from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):

    name = "rest_soundcloud"

    def set_site(self, site):
        self.site = site
        directives.register_directive('soundcloud', SoundCloud)
        directives.register_directive('soundcloud_playlist', SoundCloudPlaylist)
        return super(Plugin, self).set_site(site)


CODE = ("""<iframe width="{width}" height="{height}"
scrolling="no" frameborder="no"
src="https://w.soundcloud.com/player/?url=http://api.soundcloud.com/{preslug}/"""
        """{sid}">
</iframe>""")


class SoundCloud(Directive):
    """ Restructured text extension for inserting SoundCloud embedded music

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
    }
    preslug = "tracks"

    def run(self):
        """ Required by the Directive interface. Create docutils nodes """
        self.check_content()
        options = {
            'sid': self.arguments[0],
            'width': 600,
            'height': 160,
            'preslug': self.preslug,
        }
        options.update(self.options)
        return [nodes.raw('', CODE.format(**options), format='html')]

    def check_content(self):
        """ Emit a deprecation warning if there is content """
        if self.content:
            raise self.warning("This directive does not accept content. The "
                               "'key=value' format for options is deprecated, "
                               "use ':key: value' instead")


class SoundCloudPlaylist(SoundCloud):
    preslug = "playlists"
