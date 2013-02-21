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

import json

from docutils import nodes
from docutils.parsers.rst import Directive, directives


class slides(Directive):
    """ Restructured text extension for inserting slideshows."""
    has_content = True
    option_spec = {
        "preload": directives.flag,
        "preloadImage": directives.uri,
        "container": directives.unchanged,
        "generateNextPrev": directives.flag,
        "next": directives.unchanged,
        "prev": directives.unchanged,
        "pagination": directives.flag,
        "generatePagination": directives.flag,
        "paginationClass": directives.unchanged,
        "currentClass": directives.unchanged,
        "fadeSpeed": directives.positive_int,
        "fadeEasing": directives.unchanged,
        "slideSpeed": directives.positive_int,
        "slideEasing": directives.unchanged,
        "start": directives.positive_int,
        "effect": directives.unchanged,
        "crossfade": directives.flag,
        "randomize": directives.flag,
        "play": directives.positive_int,
        "pause": directives.positive_int,
        "hoverPause": directives.flag,
        "autoHeight": directives.flag,
        "autoHeightSpeed": directives.positive_int,
        "bigTarget": directives.flag,
        "animationStart": directives.unchanged,
        "animationComplete": directives.unchanged,
    }

    def run(self):
        if len(self.content) == 0:
            return
        for opt in ("preload", "generateNextPrev", "pagination",
                    "generatePagination", "crossfade", "randomize",
                    "hoverPause", "autoHeight", "bigTarget"):
            if opt in self.options:
                self.options[opt] = True
        options = {
            "autoHeight": True,
            "bigTarget": True,
            "paginationClass": "pager",
            "currentClass": "slide-current"
        }
        options.update(self.options)
        options = json.dumps(options)
        output = []
        output.append('<script> $(function(){ $("#slides").slides(' + options +
                      '); });'
                      '</script>')
        output.append('<div id="slides" class="slides"><div '
                      'class="slides_container">')
        for image in self.content:
            output.append("""<div><img src="{0}"></div>""".format(image))
        output.append("""</div></div>""")

        return [nodes.raw('', '\n'.join(output), format='html')]


directives.register_directive('slides', slides)
