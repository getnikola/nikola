# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Create a new site."""

from __future__ import print_function, unicode_literals
import os

import feedparser

from nikola.plugin_categories import Command
from nikola.utils import get_logger, STDERR_HANDLER, slugify, LocaleBorg, makedirs


LOGGER = get_logger('init', STDERR_HANDLER)


class CommandContinuousImport(Command):
    """Import and merge feeds into your blog."""

    name = "continuous_import"

    doc_usage = ""
    needs_config = True
    doc_purpose = "Import and merge feeds into your blog."
    cmd_options = []

    def _execute(self, options={}, args=None):
        """Import and merge feeds into your blog."""
        for name, feed in self.site.config['FEEDS'].items():
            LOGGER.info('Processing {}', name)
            items = self.fetch(feed)['entries']
            for item in items:
                self.generate(item, feed)

    def fetch(self, feed):
        url = feed['url']
        parsed = feedparser.parse(url)
        return parsed

    def generate(self, item, feed):
        compiler = self.site.compilers[feed['format']]
        title = item[feed['metadata']['title']]
        output_name = os.path.join(feed['output_folder'],
                                slugify(title, feed['lang'])) + compiler.extension()
        post = self.site.render_template(
            feed['template'],
            None,
            dict(
                item=item,
                feed=feed,
                lang=feed['lang'],
            ))
        makedirs(os.path.dirname(output_name))
        with open(output_name, "w+") as post_file:
            post_file.write(post)
