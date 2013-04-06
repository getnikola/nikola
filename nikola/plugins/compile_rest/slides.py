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

from __future__ import unicode_literals

from docutils import nodes
from docutils.parsers.rst import Directive, directives


class Slides(Directive):
    """ Restructured text extension for inserting slideshows."""
    has_content = True

    def run(self):
        if len(self.content) == 0:
            return
        output = []
        output.append("""
        <div id="myCarousel" class="carousel slide">
        <ol class="carousel-indicators">
        """)
        for i in range(len(self.content)):
            if i == 0:
                classname = 'class="active"'
            else:
                classname = ''
            output.append('  <li data-target="#myCarousel" data-slide-to="{0}" {1}></li>'.format(i, classname))
        output.append("""</ol>
        <div class="carousel-inner">
        """)
        for i, image in enumerate(self.content):
            if i == 0:
                classname = "item active"
            else:
                classname = "item"
            output.append("""<div class="{0}"><img src="{1}" alt="" style="margin: 0 auto 0 auto;"></div>""".format(classname, image))
        output.append("""</div>
                        <a class="left carousel-control" href="#myCarousel" data-slide="prev">&lsaquo;</a>
                <a class="right carousel-control" href="#myCarousel" data-slide="next">&rsaquo;</a>
                </div>""")
        return [nodes.raw('', '\n'.join(output), format='html')]


directives.register_directive('slides', Slides)
