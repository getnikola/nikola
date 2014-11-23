from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives.images import Image

from nikola.plugin_categories import RestExtension

class Plugin(RestExtension):

    name = "rest_thumbnail"

    def set_site(self, site):
        self.site = site
        directives.register_directive('thumbnail', Thumbnail)
        return super(Plugin, self).set_site(site)


class Thumbnail(Image):

    option_spec = Image.option_spec.copy()

    def run(self):
        (image_node,) = Image.run(self)
        return [image_node]
