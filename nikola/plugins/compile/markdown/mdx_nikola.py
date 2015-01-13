# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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
try:
    from markdown.postprocessors import Postprocessor
    from markdown.extensions import Extension
except ImportError:
    # No need to catch this, if you try to use this without Markdown,
    # the markdown compiler will fail first
    Postprocessor = Extension = object

from nikola.plugin_categories import MarkdownExtension

CODERE = re.compile('<div class="codehilite"><pre>(.*?)</pre></div>', flags=re.MULTILINE | re.DOTALL)


class NikolaPostProcessor(Postprocessor):
    def run(self, text):
        output = text

        # python-markdown's highlighter uses <div class="codehilite"><pre>
        # for code.  We switch it to reST's <pre class="code">.
        # TODO: monkey-patch for CodeHilite that uses nikola.utils.NikolaPygmentsHTML
        output = CODERE.sub('<pre class="code literal-block">\\1</pre>', output)
        return output


class NikolaExtension(MarkdownExtension, Extension):
    def extendMarkdown(self, md, md_globals):
        pp = NikolaPostProcessor()
        md.postprocessors.add('nikola_post_processor', pp, '_end')
        md.registerExtension(self)


def makeExtension(configs=None):
    return NikolaExtension(configs)
