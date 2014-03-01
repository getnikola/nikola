# -*- coding: utf-8 -*-


from docutils import nodes
from docutils.parsers.rst import Directive, directives


from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):

    name = "rest_spotify"

    def set_site(self, site):
        self.site = site
        directives.register_directive('spotify', Spotify)
        return super(Plugin, self).set_site(site)


CODE = ("""<iframe src="https://embed.spotify.com/?uri={spotify_uri}"
    width="{width}" height="{height}"
    frameborder="0" allowtransparency="true">
</iframe>""")


class Spotify(Directive):
    """ Restructured text extension for inserting Spotify embedded music

    Usage:
        .. spotify:: <spotify URI>
           :height: 380
           :width: 80

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
            'spotify_uri': self.arguments[0],
            'width': 380,
            'height': 80,
        }
        options.update(self.options)
        return [nodes.raw('', CODE.format(**options), format='html')]

    def check_content(self):
        """ Emit a deprecation warning if there is content """
        if self.content:
            raise self.warning("This directive does not accept content. The "
                               "'key=value' format for options is deprecated, "
                               "use ':key: value' instead")
