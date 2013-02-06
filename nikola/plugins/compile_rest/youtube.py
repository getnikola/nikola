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
from docutils.parsers.rst import directives

CODE = """\
<iframe width="%(width)s"
height="%(height)s"
src="http://www.youtube.com/embed/%(yid)s?rel=0&amp;hd=1&amp;wmode=transparent"
></iframe>"""


def youtube(name, args, options, content, lineno,
            contentOffset, blockText, state, stateMachine):
    """ Restructured text extension for inserting youtube embedded videos """
    if len(content) == 0:
        return
    string_vars = {
        'yid': content[0],
        'width': 425,
        'height': 344,
        'extra': ''
    }
    extra_args = content[1:]  # Because content[0] is ID
    extra_args = [ea.strip().split("=") for ea in extra_args]  # key=value
    extra_args = [ea for ea in extra_args if len(ea) == 2]  # drop bad lines
    extra_args = dict(extra_args)
    if 'width' in extra_args:
        string_vars['width'] = extra_args.pop('width')
    if 'height' in extra_args:
        string_vars['height'] = extra_args.pop('height')
    return [nodes.raw('', CODE % (string_vars), format='html')]
youtube.content = True
directives.register_directive('youtube', youtube)
