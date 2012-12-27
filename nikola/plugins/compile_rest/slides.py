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


def slides(name, args, options, content, lineno,
            contentOffset, blockText, state, stateMachine):
    """ Restructured text extension for inserting slideshows."""
    if len(content) == 0:
        return
    output = []
    output.append("""<script> $(function(){ $("#slides").slides({
    autoHeight: true,
    bigTarget: true,
    paginationClass: 'pager',
    currentClass: 'slide-current',
    }); }); </script>""")
    output.append("""<div id="slides" class="slides"><div class="slides_container">""")
    for image in content:
        output.append("""<div><img src="%s"></div>""" % image)
    output.append("""</div></div>""")
    
    return [nodes.raw('', '\n'.join(output), format='html')]
slides.content = True
directives.register_directive('slides', slides)
