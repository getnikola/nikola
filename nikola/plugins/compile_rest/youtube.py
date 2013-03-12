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

from docutils import nodes
from docutils.parsers.rst import Directive, directives


CODE = """\
<iframe width="{width}"
height="{height}"
src="http://www.youtube.com/embed/{yid}?rel=0&amp;hd=1&amp;wmode=transparent"
></iframe>"""


class Youtube(Directive):
    """ Restructured text extension for inserting youtube embedded videos

    Usage:
        .. youtube:: lyViVmaBQDg
           :height: 400
           :width: 600

    """
    has_content = True
    required_arguments = 1
    option_spec = {
        "width": directives.positive_int,
        "height": directives.positive_int,
    }

    def run(self):
        self.check_content()
        options = {
            'yid': self.arguments[0],
            'width': 425,
            'height': 344,
        }
        options.update(self.options)
        return [nodes.raw('', CODE.format(**options), format='html')]

    def check_content(self):
        if self.content:
            raise self.warning("This directive does not accept content. The "
                               "'key=value' format for options is deprecated, "
                               "use ':key: value' instead")


directives.register_directive('youtube', Youtube)
