# -*- coding: utf-8 -*-

# Copyright © 2015 Manuel Kaufmann

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

from __future__ import unicode_literals

import os

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):

    name = "rest_fotorama"

    def set_site(self, site):
        self.site = site
        directives.register_directive('fotorama', Fotorama)
        Fotorama.site = site
        return super(Plugin, self).set_site(site)


class Fotorama(Directive):
    """ Restructured text extension for inserting fotorama galleries."""

    # http://fotorama.io/customize/options/
    option_spec = {
        'width': directives.unchanged,
        'minwidth': directives.unchanged,
        'maxwidth': directives.unchanged,
        'height': directives.unchanged,
        'minheight': directives.unchanged,
        'maxheight': directives.unchanged,
        'ratio': directives.unchanged,
        'margin': directives.nonnegative_int,
        'glimpse': directives.unchanged,
        'nav': lambda arg: directives.choice(arg, ('dots', 'thumbs', 'false')),
        'navposition': lambda arg: directives.choice(arg, ('bottom', 'top')),
        'navwidth': directives.unchanged,
        'thumbwidth': directives.nonnegative_int,
        'thumbheight': directives.nonnegative_int,
        'thumbborderwidth': directives.nonnegative_int,
        'allowfullscreen': lambda arg: directives.choice(arg, ('false', 'true', 'native')),
        'fit': lambda arg: directives.choice(arg, ('contain', 'cover', 'scaledown', 'none')),
        'thumbfit': directives.unchanged,
        'transition': lambda arg: directives.choice(arg, ('slide', 'crossfade', 'disolve')),
        'clicktransition': directives.unchanged,
        'transitionduration': directives.nonnegative_int,
        'captions': directives.flag,
        'hash': directives.flag,
        'startindex': directives.unchanged,
        'loop': directives.flag,
        'autoplay': directives.unchanged,
        'stopautoplayontouch': directives.unchanged,
        'keyboard': directives.unchanged,
        'arrows': lambda arg: directives.choice(arg, ('true', 'false', 'always')),
        'click': directives.flag,
        'swipe': directives.flag,
        'trackpad': directives.flag,
        'shuffle': directives.flag,
        'direction': lambda arg: directives.choice(arg, ('ltr', 'rtl')),
        'spinner': directives.unchanged,
        'shadows': directives.flag,
    }
    has_content = True

    def _sanitize_options(self):
        defaults = {
            'nav': 'thumbs',
            'ratio': '16/9',
            'keyboard': 'true',
            'thumb-width': 128,
            'thumb-height': 128,
            'allowfullscreen': 'native'
        }
        defaults = self.site.config.get('FOTORAMA_OPTIONS', defaults)

        # TODO: validate options here and (maybe) display an error
        defaults.update(self.options)
        return defaults

    def run(self):
        if len(self.content) == 0:
            return

        image_list = [t for t in self.content]
        thumbs = ['.thumbnail'.join(os.path.splitext(p)) for p in image_list]

        photo_array = []
        for img, thumb in zip(image_list, thumbs):
            photo_array.append({
                'url': img,
                'url_thumb': thumb,
            })

        output = self.site.template_system.render_template(
            'embedded-fotorama.tmpl',
            None,
            {
                'fotorama_content': photo_array,
                'options': self._sanitize_options()
            }
        )
        return [nodes.raw('', output, format='html')]


directives.register_directive('fotorama', Fotorama)
