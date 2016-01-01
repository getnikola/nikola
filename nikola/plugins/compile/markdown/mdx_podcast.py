# -*- coding: utf-8 -*-
#
# Copyright © 2013-2016 Michael Rabbitt, Roberto Alsina and others.
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
# Inspired by "[Python] reStructuredText GitHub Podcast directive"
# (https://gist.github.com/brianhsu/1407759), public domain by Brian Hsu

"""
Extension to Python Markdown for Embedded Audio.

Basic Example:

>>> import markdown
>>> text = "[podcast]https://archive.org/download/Rebeldes_Stereotipos/rs20120609_1.mp3[/podcast]"
>>> html = markdown.markdown(text, [PodcastExtension()])
>>> print(html)
<p><audio controls=""><source src="https://archive.org/download/Rebeldes_Stereotipos/rs20120609_1.mp3" type="audio/mpeg"></source></audio></p>
"""

from __future__ import print_function, unicode_literals
from nikola.plugin_categories import MarkdownExtension
try:
    from markdown.extensions import Extension
    from markdown.inlinepatterns import Pattern
    from markdown.util import etree
except ImportError:
    # No need to catch this, if you try to use this without Markdown,
    # the markdown compiler will fail first
    Pattern = Extension = object

PODCAST_RE = r'\[podcast\](?P<url>.+)\[/podcast\]'


class PodcastPattern(Pattern):
    """InlinePattern for footnote markers in a document's body text."""

    def __init__(self, pattern, configs):
        """Initialize pattern."""
        Pattern.__init__(self, pattern)

    def handleMatch(self, m):
        """Handle pattern matches."""
        url = m.group('url').strip()
        audio_elem = etree.Element('audio')
        audio_elem.set('controls', '')
        source_elem = etree.SubElement(audio_elem, 'source')
        source_elem.set('src', url)
        source_elem.set('type', 'audio/mpeg')
        return audio_elem


class PodcastExtension(MarkdownExtension, Extension):
    """"Podcast extension for Markdown."""

    def __init__(self, configs={}):
        """Initialize extension."""
        # set extension defaults
        self.config = {}

        # Override defaults with user settings
        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        """Extend Markdown."""
        podcast_md_pattern = PodcastPattern(PODCAST_RE, self.getConfigs())
        podcast_md_pattern.md = md
        md.inlinePatterns.add('podcast', podcast_md_pattern, "<not_strong")
        md.registerExtension(self)


def makeExtension(configs=None):  # pragma: no cover
    """Make Markdown extension."""
    return PodcastExtension(configs)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=(doctest.NORMALIZE_WHITESPACE +
                                 doctest.REPORT_NDIFF))
