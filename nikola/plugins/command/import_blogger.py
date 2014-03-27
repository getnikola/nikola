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

LOGGER = utils.get_logger('import_blogger', utils.STDERR_HANDLER)


class CommandImportBlogger(Command, ImportMixin):
    """Import a blogger dump."""

    name = "import_blogger"
    needs_config = False
    doc_usage = "[options] blogger_export_file"
    doc_purpose = "import a blogger dump"
    cmd_options = ImportMixin.cmd_options + [
        {
            'name': 'exclude_drafts',
            'long': 'no-drafts',
            'short': 'd',
            'default': False,
            'type': bool,
            'help': "Don't import drafts",
        },
    ]

    def _execute(self, options, args):
        """Import a Blogger blog from an export file into a Nikola site."""
        # Parse the data
        if feedparser is None:
            req_missing(['feedparser'], 'import Blogger dumps')
            return

        if not args:
            print(self.help())
            return

        options['filename'] = args[0]
        self.blogger_export_file = options['filename']
        self.output_folder = options['output_folder']
        self.import_into_existing_site = False
        self.exclude_drafts = options['exclude_drafts']
        self.url_map = {}
        channel = self.get_channel_from_file(self.blogger_export_file)
        self.context = self.populate_context(channel)
        conf_template = self.generate_base_site()
        self.context['REDIRECTIONS'] = self.configure_redirections(
            self.url_map)

        self.import_posts(channel)
        self.write_urlmap_csv(
            os.path.join(self.output_folder, 'url_map.csv'), self.url_map)

        conf_out_path = self.get_configuration_output_path()
        # if it tracebacks here, look a comment in
        # basic_import.Import_Mixin.generate_base_site
        conf_template_render = conf_template.render(**prepare_config(self.context))
        self.write_configuration(conf_out_path, conf_template_render)

    @classmethod
    def get_channel_from_file(cls, filename):
        if not os.path.isfile(filename):
            raise Exception("Missing file: %s" % filename)
        return feedparser.parse(filename)

    @staticmethod
    def populate_context(channel):
        context = SAMPLE_CONF.copy()
        # blogger doesn't include the language in the dump
        context['DEFAULT_LANG'] = 'en'
        context['BLOG_TITLE'] = channel.feed.title

        context['BLOG_DESCRIPTION'] = ''  # Missing in the dump
        context['SITE_URL'] = channel.feed.link
        context['BLOG_EMAIL'] = channel.feed.author_detail.email
        context['BLOG_AUTHOR'] = channel.feed.author_detail.name
        context['POSTS'] = '''(
            ("posts/*.txt", "posts", "post.tmpl"),
            ("posts/*.rst", "posts", "post.tmpl"),
            ("posts/*.html", "posts", "post.tmpl"),
            )'''
        context['PAGES'] = '''(
            ("articles/*.txt", "articles", "story.tmpl"),
            ("articles/*.rst", "articles", "story.tmpl"),
            )'''
        context['COMPILERS'] = '''{
            "rest": ('.txt', '.rst'),
            "markdown": ('.md', '.mdown', '.markdown', '.wp'),
            "html": ('.html', '.htm')
            }
            '''

        return context

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

        for candidate in item.content:
            if candidate.type == 'text/html':
                content = candidate.value
                break
                #  FIXME: handle attachments

        tags = []
        for tag in item.tags:
            if tag.scheme == 'http://www.blogger.com/atom/ns#':
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

    def process_item(self, item):
        post_type = item.tags[0].term

        if post_type == 'http://schemas.google.com/blogger/2008/kind#post':
            self.import_item(item, 'posts')
        elif post_type == 'http://schemas.google.com/blogger/2008/kind#page':
            self.import_item(item, 'stories')
        elif post_type == ('http://schemas.google.com/blogger/2008/kind'
                           '#settings'):
            # Ignore settings
            pass
        elif post_type == ('http://schemas.google.com/blogger/2008/kind'
                           '#template'):
            # Ignore template
            pass
        elif post_type == ('http://schemas.google.com/blogger/2008/kind'
                           '#comment'):
            # FIXME: not importing comments. Does blogger support "pages"?
            pass
        else:
            LOGGER.warn("Unknown post_type:", post_type)

    def import_posts(self, channel):
        for item in channel.entries:
            self.process_item(item)
