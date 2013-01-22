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

"""Markdown Extension for Nikola-specific post-processing"""
from __future__ import unicode_literals
import re
from markdown.postprocessors import Postprocessor
from markdown.extensions import Extension


class NikolaPostProcessor(Postprocessor):
    def run(self, text):
        output = text
        # h1 is reserved for the title so increment all header levels
        for n in reversed(range(1, 9)):
            output = re.sub('<h%i>' % n, '<h%i>' % (n + 1), output)
            output = re.sub('</h%i>' % n, '</h%i>' % (n + 1), output)

        # python-markdown's highlighter uses the class 'codehilite' to wrap
        # code, instead of the standard 'code'. None of the standard
        # pygments stylesheets use this class, so swap it to be 'code'
        output = re.sub(r'(<div[^>]+class="[^"]*)codehilite([^>]+)',
                        r'\1code\2', output)
        return output


class NikolaExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        pp = NikolaPostProcessor()
        md.postprocessors.add('nikola_post_processor', pp, '_end')
        md.registerExtension(self)


def makeExtension(configs=None):
    return NikolaExtension(configs)
