# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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

from __future__ import unicode_literals, print_function
import datetime
import os
import time

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # NOQA

try:
    import feedparser
except ImportError:
    feedparser = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils
from nikola.utils import req_missing
from nikola.plugins.basic_import import ImportMixin
from nikola.plugins.command.init import SAMPLE_CONF, prepare_config

LOGGER = utils.get_logger('import_feed', utils.STDERR_HANDLER)


class CommandImportFeed(Command, ImportMixin):
    """Import a feed dump."""

    name = "import_feed"
    needs_config = False
    doc_usage = "[options] feed_file"
    doc_purpose = "import a RSS/Atom dump"
    cmd_options = ImportMixin.cmd_options

    def _execute(self, options, args):
        '''
            Import Atom/RSS feed
        '''
        if feedparser is None:
            req_missing(['feedparser'], 'import feeds')
            return

        if not args:
            print(self.help())
            return

        options['filename'] = args[0]
        self.feed_export_file = options['filename']
        self.output_folder = options['output_folder']
        self.import_into_existing_site = False
        self.url_map = {}
        channel = self.get_channel_from_file(self.feed_export_file)
        self.context = self.populate_context(channel)
        conf_template = self.generate_base_site()
        self.context['REDIRECTIONS'] = self.configure_redirections(
            self.url_map)

        self.import_posts(channel)

        self.write_configuration(self.get_configuration_output_path(
        ), conf_template.render(**prepare_config(self.context)))

    @classmethod
    def get_channel_from_file(cls, filename):
        return feedparser.parse(filename)

    @staticmethod
    def populate_context(channel):
        context = SAMPLE_CONF.copy()
        context['DEFAULT_LANG'] = channel.feed.title_detail.language \
            if channel.feed.title_detail.language else 'en'
        context['BLOG_TITLE'] = channel.feed.title

        context['BLOG_DESCRIPTION'] = channel.feed.get('subtitle', '')
        context['SITE_URL'] = channel.feed.get('link', '').rstrip('/')
        context['BLOG_EMAIL'] = channel.feed.author_detail.get('email', '') if 'author_detail' in channel.feed else ''
        context['BLOG_AUTHOR'] = channel.feed.author_detail.get('name', '') if 'author_detail' in channel.feed else ''

        context['POSTS'] = '''(
            ("posts/*.html", "posts", "post.tmpl"),
        )'''
        context['PAGES'] = '''(
            ("stories/*.html", "stories", "story.tmpl"),
        )'''
        context['COMPILERS'] = '''{
        "rest": ('.txt', '.rst'),
        "markdown": ('.md', '.mdown', '.markdown', '.wp'),
        "html": ('.html', '.htm')
        }
        '''

        return context

    def import_posts(self, channel):
        for item in channel.entries:
            self.process_item(item)

    def process_item(self, item):
        self.import_item(item, 'posts')

    def import_item(self, item, out_folder=None):
        """Takes an item from the feed and creates a post file."""
        if out_folder is None:
            out_folder = 'posts'

        # link is something like http://foo.com/2012/09/01/hello-world/
        # So, take the path, utils.slugify it, and that's our slug
        link = item.link
        link_path = urlparse(link).path

        title = item.title

        # blogger supports empty titles, which Nikola doesn't
        if not title:
            LOGGER.warn("Empty title in post with URL {0}. Using NO_TITLE "
                        "as placeholder, please fix.".format(link))
            title = "NO_TITLE"

        if link_path.lower().endswith('.html'):
            link_path = link_path[:-5]

        slug = utils.slugify(link_path)

        if not slug:  # should never happen
            LOGGER.error("Error converting post:", title)
            return

        description = ''
        post_date = datetime.datetime.fromtimestamp(time.mktime(
            item.published_parsed))
        if item.get('content'):
            for candidate in item.get('content', []):
                content = candidate.value
                break
                #  FIXME: handle attachments
        elif item.get('summary'):
            content = item.get('summary')

        tags = []
        for tag in item.get('tags', []):
            tags.append(tag.term)

        if item.get('app_draft'):
            tags.append('draft')
            is_draft = True
        else:
            is_draft = False

        self.url_map[link] = self.context['SITE_URL'] + '/' + \
            out_folder + '/' + slug + '.html'

        if is_draft and self.exclude_drafts:
            LOGGER.notice('Draft "{0}" will not be imported.'.format(title))
        elif content.strip():
            # If no content is found, no files are written.
            content = self.transform_content(content)

            self.write_metadata(os.path.join(self.output_folder, out_folder,
                                             slug + '.meta'),
                                title, slug, post_date, description, tags)
            self.write_content(
                os.path.join(self.output_folder, out_folder, slug + '.html'),
                content)
        else:
            LOGGER.warn('Not going to import "{0}" because it seems to contain'
                        ' no content.'.format(title))

    @staticmethod
    def write_metadata(filename, title, slug, post_date, description, tags):
        ImportMixin.write_metadata(filename,
                                   title,
                                   slug,
                                   post_date.strftime(r'%Y/%m/%d %H:%m:%S'),
                                   description,
                                   tags)
