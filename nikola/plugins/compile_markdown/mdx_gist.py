# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Michael Rabbitt.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Inspired by "[Python] reStructuredText GitHub Gist directive"
# (https://gist.github.com/brianhsu/1407759), public domain by Brian Hsu

from __future__ import print_function


'''
Extension to Python Markdown for Embedded Gists (gist.github.com)

Basic Example:

    >>> import markdown
    >>> text = """
    ... Text of the gist:
    ... [:gist: 4747847]
    ... """
    >>> html = markdown.markdown(text, [GistExtension()])
    >>> print(html)
    <p>Text of the gist:
    <div class="gist">
    <script src="https://gist.github.com/4747847.js"></script>
    <noscript>
    <pre>import this</pre>
    </noscript>
    </div>
    </p>

Example with filename:

    >>> import markdown
    >>> text = """
    ... Text of the gist:
    ... [:gist: 4747847 zen.py]
    ... """
    >>> html = markdown.markdown(text, [GistExtension()])
    >>> print(html)
    <p>Text of the gist:
    <div class="gist">
    <script src="https://gist.github.com/4747847.js?file=zen.py"></script>
    <noscript>
    <pre>import this</pre>
    </noscript>
    </div>
    </p>

Example using reStructuredText syntax:

    >>> import markdown
    >>> text = """
    ... Text of the gist:
    ... .. gist:: 4747847 zen.py
    ... """
    >>> html = markdown.markdown(text, [GistExtension()])
    >>> print(html)
    <p>Text of the gist:
    <div class="gist">
    <script src="https://gist.github.com/4747847.js?file=zen.py"></script>
    <noscript>
    <pre>import this</pre>
    </noscript>
    </div>
    </p>
'''
from __future__ import unicode_literals
import warnings
from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import AtomicString
from markdown.util import etree

try:
    import requests
except ImportError:
    requests = None  # NOQA

GIST_JS_URL = "https://gist.github.com/{0}.js"
GIST_FILE_JS_URL = "https://gist.github.com/{0}.js?file={1}"
GIST_RAW_URL = "https://raw.github.com/gist/{0}"
GIST_FILE_RAW_URL = "https://raw.github.com/gist/{0}/{1}"

GIST_MD_RE = r'\[:gist:\s*(?P<gist_id>\d+)(?:\s*(?P<filename>.+?))?\]'
GIST_RST_RE = r'(?m)^\.\.\s*gist::\s*(?P<gist_id>\d+)(?:\s*(?P<filename>.+))\s*$'


class GistPattern(Pattern):
    """ InlinePattern for footnote markers in a document's body text. """

    def __init__(self, pattern, configs):
        Pattern.__init__(self, pattern)

    def get_raw_gist_with_filename(self, gist_id, filename):
        url = GIST_FILE_RAW_URL.format(gist_id, filename)
        return requests.get(url).text

    def get_raw_gist(self, gist_id):
        url = GIST_RAW_URL.format(gist_id)
        return requests.get(url).text

    def handleMatch(self, m):
        gist_id = m.group('gist_id')
        gist_file = m.group('filename')

        gist_elem = etree.Element('div')
        gist_elem.set('class', 'gist')
        script_elem = etree.SubElement(gist_elem, 'script')

        if gist_file:
            script_elem.set('src', GIST_FILE_JS_URL.format(
                gist_id, gist_file))

        else:
            script_elem.set('src', GIST_JS_URL.format(
                gist_id))

        if requests:
            if gist_file:
                raw_gist = (self.get_raw_gist_with_filename(
                    gist_id, gist_file))
                script_elem.set('src', GIST_FILE_JS_URL.format(
                    gist_id, gist_file))

            else:
                raw_gist = (self.get_raw_gist(gist_id))
                script_elem.set('src', GIST_JS_URL.format(
                    gist_id))

            # Insert source as <pre/> within <noscript>
            noscript_elem = etree.SubElement(gist_elem, 'noscript')
            pre_elem = etree.SubElement(noscript_elem, 'pre')
            pre_elem.text = AtomicString(raw_gist)

        else:
            warnings.warn('"requests" package not installed.  '
                          'Please install to add inline gist source.')

        return gist_elem


class GistExtension(Extension):
    def __init__(self, configs={}):
        # set extension defaults
        self.config = {}

        # Override defaults with user settings
        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        gist_md_pattern = GistPattern(GIST_MD_RE, self.getConfigs())
        gist_md_pattern.md = md
        md.inlinePatterns.add('gist', gist_md_pattern, "<not_strong")

        gist_rst_pattern = GistPattern(GIST_RST_RE, self.getConfigs())
        gist_rst_pattern.md = md
        md.inlinePatterns.add('gist-rst', gist_rst_pattern, ">gist")

        md.registerExtension(self)


def makeExtension(configs=None):
    return GistExtension(configs)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=(doctest.NORMALIZE_WHITESPACE +
                                 doctest.REPORT_NDIFF))
