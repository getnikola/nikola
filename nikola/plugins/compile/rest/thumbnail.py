import os

from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives.images import Image, Figure

from nikola.plugin_categories import RestExtension

class Plugin(RestExtension):

    name = "rest_thumbnail"

    def set_site(self, site):
        self.site = site
        directives.register_directive('thumbnail', Thumbnail)
        return super(Plugin, self).set_site(site)


class Thumbnail(Figure):

    def align(argument):
        return directives.choice(argument, Image.align_values)

    def figwidth_value(argument):
        if argument.lower() == 'image':
            return 'image'
        else:
            return directives.length_or_percentage_or_unitless(argument, 'px')

    option_spec = Image.option_spec.copy()
    option_spec['figwidth'] = figwidth_value
    option_spec['figclass'] = directives.class_option
    has_content = True

    def run(self):
        uri = directives.uri(self.arguments[0])
        self.options['target'] = uri
        self.arguments[0] = '.thumbnail'.join(os.path.splitext(uri))
        if self.content:
            (node,) = Figure.run(self)
        else:
            (node,) = Image.run(self)
        return [node]
