# -*- coding: utf-8 -*-
#
# Copyright © 2013 Michael Rabbitt.
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
# Warning: URL formats of "raw" gists are undocummented and subject to change.
# See also:  https://developer.github.com/v3/gists/
#
# Inspired by "[Python] reStructuredText GitHub Gist directive"
# (https://gist.github.com/brianhsu/1407759), public domain by Brian Hsu
"""
Extension to Python Markdown for Embedded Gists (gist.github.com).

Basic Example:

    Text of the gist:
    [:gist: 4747847]

Example with filename:

    Text of the gist:
    [:gist: 4747847 zen.py]

Basic Example with hexidecimal id:

    Text of the gist:
    [:gist: c4a43d6fdce612284ac0]

Example with hexidecimal id filename:

    Text of the gist:
    [:gist: c4a43d6fdce612284ac0 cow.txt]

Example using reStructuredText syntax:

    Text of the gist:
    .. gist:: 4747847 zen.py

Example using hexidecimal ID with reStructuredText syntax:

    Text of the gist:
    .. gist:: c4a43d6fdce612284ac0

Example using hexidecimal ID and filename with reStructuredText syntax:

    Text of the gist:
    .. gist:: c4a43d6fdce612284ac0 cow.txt

Error Case: non-existent Gist ID:

    Text of the gist:
    [:gist: 0]

Error Case: non-existent file:

    Text of the gist:
    [:gist: 4747847 doesntexist.py]
"""

from __future__ import unicode_literals, print_function

try:
    from markdown.extensions import Extension
    from markdown.inlinepatterns import Pattern
    from markdown.util import AtomicString
    from markdown.util import etree
except ImportError:
    # No need to catch this, if you try to use this without Markdown,
    # the markdown compiler will fail first
    Extension = Pattern = object

from nikola.plugin_categories import MarkdownExtension
from nikola.utils import get_logger, STDERR_HANDLER

import requests

LOGGER = get_logger('compile_markdown.mdx_gist', STDERR_HANDLER)

GIST_JS_URL = "https://gist.github.com/{0}.js"
GIST_FILE_JS_URL = "https://gist.github.com/{0}.js?file={1}"
GIST_RAW_URL = "https://gist.githubusercontent.com/raw/{0}"
GIST_FILE_RAW_URL = "https://gist.githubusercontent.com/raw/{0}/{1}"

GIST_MD_RE = r'\[:gist:\s*(?P<gist_id>\S+)(?:\s*(?P<filename>.+?))?\s*\]'
GIST_RST_RE = r'(?m)^\.\.\s*gist::\s*(?P<gist_id>[^\]\s]+)(?:\s*(?P<filename>.+?))?\s*$'


class GistFetchException(Exception):
    """Raised when attempt to fetch content of a Gist from github.com fails."""

    def __init__(self, url, status_code):
        """Initialize the exception."""
        Exception.__init__(self)
        self.message = 'Received a {0} response from Gist URL: {1}'.format(
            status_code, url)


class GistPattern(Pattern):
    """InlinePattern for footnote markers in a document's body text."""

    def __init__(self, pattern, configs):
        """Initialize the pattern."""
        Pattern.__init__(self, pattern)

    def get_raw_gist_with_filename(self, gist_id, filename):
        """Get raw gist text for a filename."""
        url = GIST_FILE_RAW_URL.format(gist_id, filename)
        resp = requests.get(url)

        if not resp.ok:
            raise GistFetchException(url, resp.status_code)

        return resp.text

    def get_raw_gist(self, gist_id):
        """Get raw gist text."""
        url = GIST_RAW_URL.format(gist_id)
        resp = requests.get(url)

        if not resp.ok:
            raise GistFetchException(url, resp.status_code)

        return resp.text

    def handleMatch(self, m):
        """Handle pattern match."""
        gist_id = m.group('gist_id')
        gist_file = m.group('filename')

        gist_elem = etree.Element('div')
        gist_elem.set('class', 'gist')
        script_elem = etree.SubElement(gist_elem, 'script')

        noscript_elem = etree.SubElement(gist_elem, 'noscript')

        try:
            if gist_file:
                script_elem.set('src', GIST_FILE_JS_URL.format(
                    gist_id, gist_file))
                raw_gist = (self.get_raw_gist_with_filename(
                    gist_id, gist_file))

            else:
                script_elem.set('src', GIST_JS_URL.format(gist_id))
                raw_gist = (self.get_raw_gist(gist_id))

            # Insert source as <pre/> within <noscript>
            pre_elem = etree.SubElement(noscript_elem, 'pre')
            pre_elem.text = AtomicString(raw_gist)

        except GistFetchException as e:
            LOGGER.warn(e.message)
            warning_comment = etree.Comment(' WARNING: {0} '.format(e.message))
            noscript_elem.append(warning_comment)

        return gist_elem


class GistExtension(MarkdownExtension, Extension):
    """Gist extension for Markdown."""

    def __init__(self, configs={}):
        """Initialize the extension."""
        # set extension defaults
        self.config = {}

        # Override defaults with user settings
        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        """Extend Markdown."""
        gist_md_pattern = GistPattern(GIST_MD_RE, self.getConfigs())
        gist_md_pattern.md = md
        md.inlinePatterns.add('gist', gist_md_pattern, "<not_strong")

        gist_rst_pattern = GistPattern(GIST_RST_RE, self.getConfigs())
        gist_rst_pattern.md = md
        md.inlinePatterns.add('gist-rst', gist_rst_pattern, ">gist")

        md.registerExtension(self)


def makeExtension(configs=None):  # pragma: no cover
    """Make Markdown extension."""
    return GistExtension(configs)

if __name__ == '__main__':
    import doctest

    doctest.testmod(optionflags=(doctest.NORMALIZE_WHITESPACE +
                                 doctest.REPORT_NDIFF))
