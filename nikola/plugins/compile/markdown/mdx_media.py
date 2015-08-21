# -*- coding: utf-8 -*-
#
# Copyright © 2013-2015 Michael Rabbitt, Roberto Alsina and others.
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
# Inspired by "[Python] reStructuredText GitHub Media directive"
# (https://gist.github.com/brianhsu/1407759), public domain by Brian Hsu

"""
Extension to Python Markdown for Embedded Audio.

Basic Example:

>>> import markdown
>>> text = "[media]http://www.youtube.com/watch?v=54XHDUOHuzU[/media]"
>>> print(markdown.markdown(text, [MediaExtension()]))

<iframe width="459" height="344" src="https://www.youtube.com/embed/54XHDUOHuzU?feature=oembed" frameborder="0" allowfullscreen></iframe>
"""

from __future__ import print_function, unicode_literals
from nikola.plugin_categories import MarkdownExtension
import lxml.html
try:
    from markdown.extensions import Extension
    from markdown.inlinepatterns import Pattern
    from markdown.util import etree
except ImportError:
    # No need to catch this, if you try to use this without Markdown,
    # the markdown compiler will fail first
    Pattern = Extension = object
try:
    import micawber
except ImportError:
    micawber = None  # NOQA


MEDIA_RE = r'\[media\](?P<url>.+)\[/media\]'


class MediaPattern(Pattern):

    """InlinePattern for media embedding using OpenEmbed."""

    def __init__(self, pattern, configs):
        """Initialize pattern."""
        Pattern.__init__(self, pattern)
        self.parser = etree.HTMLParser()
        if micawber:
            self.providers = micawber.bootstrap_basic()

    def handleMatch(self, m):
        """Handle pattern matches."""
        if micawber is None:
            msg = req_missing(['micawber'], 'use the media directive', optional=True)
            return None

        url = m.group('url').strip()
        data = micawber.parse_text(url, self.providers)

        # BOOOO for some sources micawber creates unparseable data
        return etree.fromstring(data, self.parser).find('body').getchildren()[0]


class MediaExtension(MarkdownExtension, Extension):

    """"Media extension for Markdown."""

    def __init__(self, configs={}):
        """Initialize extension."""
        # set extension defaults
        self.config = {}

        # Override defaults with user settings
        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        """Extend Markdown."""
        podcast_md_pattern = MediaPattern(MEDIA_RE, self.getConfigs())
        podcast_md_pattern.md = md
        md.inlinePatterns.add('media', podcast_md_pattern, "<not_strong")
        md.registerExtension(self)


def makeExtension(configs=None):  # pragma: no cover
    """Make Markdown extension."""
    return MediaExtension(configs)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=(doctest.NORMALIZE_WHITESPACE +
                                 doctest.REPORT_NDIFF))
