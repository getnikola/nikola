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

from __future__ import unicode_literals, print_function
import os
import re
from lxml import etree

try:
    from urlparse import urlparse
    from urllib import unquote
except ImportError:
    from urllib.parse import urlparse, unquote  # NOQA

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils
from nikola.plugins.basic_import import ImportMixin, links


class CommandImportWordpress(Command, ImportMixin):
    """Import a wordpress dump."""

    name = "import_wordpress"
    needs_config = False
    doc_usage = "[options] wordpress_export_file"
    doc_purpose = "Import a wordpress dump."
    cmd_options = ImportMixin.cmd_options + [
        {
            'name': 'exclude_drafts',
            'long': 'no-drafts',
            'short': 'd',
            'default': False,
            'type': bool,
            'help': "Don't import drafts",
        },
        {
            'name': 'squash_newlines',
            'long': 'squash-newlines',
            'default': False,
            'type': bool,
            'help': "Shorten multiple newlines in a row to only two newlines",
        },
        {
            'name': 'no_downloads',
            'long': 'no-downloads',
            'default': False,
            'type': bool,
            'help': "Do not try to download files for the import",
        },
    ]

    def _execute(self, options={}, args=[]):
        """Import a Wordpress blog from an export file into a Nikola site."""
        # Parse the data
        if requests is None:
            print('To use the import_wordpress command,'
                  ' you have to install the "requests" package.')
            return

        if not args:
            print(self.help())
            return

        options['filename'] = args.pop(0)

        if args and ('output_folder' not in args or
                     options['output_folder'] == 'new_site'):
            options['output_folder'] = args.pop(0)

        if args:
            print('You specified additional arguments ({0}). Please consider '
                  'putting these arguments before the filename if you '
                  'are running into problems.'.format(args))

        self.wordpress_export_file = options['filename']
        self.squash_newlines = options.get('squash_newlines', False)
        self.no_downloads = options.get('no_downloads', False)
        self.output_folder = options.get('output_folder', 'new_site')
        self.import_into_existing_site = False
        self.exclude_drafts = options.get('exclude_drafts', False)
        self.url_map = {}
        channel = self.get_channel_from_file(self.wordpress_export_file)
        self.context = self.populate_context(channel)
        conf_template = self.generate_base_site()
        self.timezone = None

        self.import_posts(channel)

        self.context['REDIRECTIONS'] = self.configure_redirections(
            self.url_map)
        self.write_urlmap_csv(
            os.path.join(self.output_folder, 'url_map.csv'), self.url_map)
        rendered_template = conf_template.render(**self.context)
        rendered_template = re.sub('# REDIRECTIONS = ', 'REDIRECTIONS = ',
                                   rendered_template)
        if self.timezone:
            rendered_template = re.sub('# TIMEZONE = \'Europe/Zurich\'',
                                       'TIMEZONE = \'' + self.timezone + '\'',
                                       rendered_template)
        self.write_configuration(self.get_configuration_output_path(),
                                 rendered_template)

    @classmethod
    def _glue_xml_lines(cls, xml):
        new_xml = xml[0]
        previous_line_ended_in_newline = new_xml.endswith(b'\n')
        previous_line_was_indentet = False
        for line in xml[1:]:
            if (re.match(b'^[ \t]+', line) and previous_line_ended_in_newline):
                new_xml = b''.join((new_xml, line))
                previous_line_was_indentet = True
            elif previous_line_was_indentet:
                new_xml = b''.join((new_xml, line))
                previous_line_was_indentet = False
            else:
                new_xml = b'\n'.join((new_xml, line))
                previous_line_was_indentet = False

            previous_line_ended_in_newline = line.endswith(b'\n')

        return new_xml

    @classmethod
    def read_xml_file(cls, filename):
        xml = []

        with open(filename, 'rb') as fd:
            for line in fd:
                # These explode etree and are useless
                if b'<atom:link rel=' in line:
                    continue
                xml.append(line)

        return cls._glue_xml_lines(xml)

    @classmethod
    def get_channel_from_file(cls, filename):
        tree = etree.fromstring(cls.read_xml_file(filename))
        channel = tree.find('channel')
        return channel

    @staticmethod
    def populate_context(channel):
        wordpress_namespace = channel.nsmap['wp']

        context = {}
        context['DEFAULT_LANG'] = get_text_tag(channel, 'language', 'en')[:2]
        context['BLOG_TITLE'] = get_text_tag(channel, 'title',
                                             'PUT TITLE HERE')
        context['BLOG_DESCRIPTION'] = get_text_tag(
            channel, 'description', 'PUT DESCRIPTION HERE')
        context['BASE_URL'] = get_text_tag(channel, 'link', '#')
        if not context['BASE_URL']:
            base_site_url = channel.find('{{{0}}}author'.format(wordpress_namespace))
            context['BASE_URL'] = get_text_tag(base_site_url,
                                               None,
                                               "http://foo.com")
        context['SITE_URL'] = context['BASE_URL']

        author = channel.find('{{{0}}}author'.format(wordpress_namespace))
        context['BLOG_EMAIL'] = get_text_tag(
            author,
            '{{{0}}}author_email'.format(wordpress_namespace),
            "joe@example.com")
        context['BLOG_AUTHOR'] = get_text_tag(
            author,
            '{{{0}}}author_display_name'.format(wordpress_namespace),
            "Joe Example")
        context['POST_PAGES'] = '''(
            ("posts/*.wp", "posts", "post.tmpl", True),
            ("stories/*.wp", "stories", "story.tmpl", False),
        )'''
        context['POST_COMPILERS'] = '''{
        "rest": ('.txt', '.rst'),
        "markdown": ('.md', '.mdown', '.markdown', '.wp'),
        "html": ('.html', '.htm')
        }
        '''

        return context

    def download_url_content_to_file(self, url, dst_path):
        if self.no_downloads:
            return

        try:
            with open(dst_path, 'wb+') as fd:
                fd.write(requests.get(url).content)
        except requests.exceptions.ConnectionError as err:
            print("Downloading {0} to {1} failed: {2}".format(url, dst_path,
                                                              err))

    def import_attachment(self, item, wordpress_namespace):
        url = get_text_tag(
            item, '{{{0}}}attachment_url'.format(wordpress_namespace), 'foo')
        link = get_text_tag(item, '{{{0}}}link'.format(wordpress_namespace),
                            'foo')
        path = urlparse(url).path
        dst_path = os.path.join(*([self.output_folder, 'files']
                                  + list(path.split('/'))))
        dst_dir = os.path.dirname(dst_path)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        print("Downloading {0} => {1}".format(url, dst_path))
        self.download_url_content_to_file(url, dst_path)
        dst_url = '/'.join(dst_path.split(os.sep)[2:])
        links[link] = '/' + dst_url
        links[url] = '/' + dst_url

    @staticmethod
    def transform_sourcecode(content):
        new_content = re.sub('\[sourcecode language="([^"]+)"\]',
                             "\n~~~~~~~~~~~~{.\\1}\n", content)
        new_content = new_content.replace('[/sourcecode]',
                                          "\n~~~~~~~~~~~~\n")
        return new_content

    @staticmethod
    def transform_caption(content):
        new_caption = re.sub(r'\[/caption\]', '', content)
        new_caption = re.sub(r'\[caption.*\]', '', new_caption)

        return new_caption

    def transform_multiple_newlines(self, content):
        """Replaces multiple newlines with only two."""
        if self.squash_newlines:
            return re.sub(r'\n{3,}', r'\n\n', content)
        else:
            return content

    def transform_content(self, content):
        new_content = self.transform_sourcecode(content)
        new_content = self.transform_caption(new_content)
        new_content = self.transform_multiple_newlines(new_content)
        return new_content

    def import_item(self, item, wordpress_namespace, out_folder=None):
        """Takes an item from the feed and creates a post file."""
        if out_folder is None:
            out_folder = 'posts'

        title = get_text_tag(item, 'title', 'NO TITLE')
        # link is something like http://foo.com/2012/09/01/hello-world/
        # So, take the path, utils.slugify it, and that's our slug
        link = get_text_tag(item, 'link', None)
        path = unquote(urlparse(link).path)

        # In python 2, path is a str. slug requires a unicode
        # object. According to wikipedia, unquoted strings will
        # usually be UTF8
        if isinstance(path, utils.bytes_str):
            path = path.decode('utf8')
        slug = utils.slugify(path)
        if not slug:  # it happens if the post has no "nice" URL
            slug = get_text_tag(
                item, '{{{0}}}post_name'.format(wordpress_namespace), None)
        if not slug:  # it *may* happen
            slug = get_text_tag(
                item, '{{{0}}}post_id'.format(wordpress_namespace), None)
        if not slug:  # should never happen
            print("Error converting post:", title)
            return

        description = get_text_tag(item, 'description', '')
        post_date = get_text_tag(
            item, '{{{0}}}post_date'.format(wordpress_namespace), None)
        dt = utils.to_datetime(post_date)
        if dt.tzinfo and self.timezone is None:
            self.timezone = utils.get_tzname(dt)
        status = get_text_tag(
            item, '{{{0}}}status'.format(wordpress_namespace), 'publish')
        content = get_text_tag(
            item, '{http://purl.org/rss/1.0/modules/content/}encoded', '')

        tags = []
        if status == 'trash':
            print('Trashed post "{0}" will not be imported.'.format(title))
            return
        elif status != 'publish':
            tags.append('draft')
            is_draft = True
        else:
            is_draft = False

        for tag in item.findall('category'):
            text = tag.text
            if text == 'Uncategorized':
                continue
            tags.append(text)

        if is_draft and self.exclude_drafts:
            print('Draft "{0}" will not be imported.'.format(title))
        elif content.strip():
            # If no content is found, no files are written.
            self.url_map[link] = self.context['SITE_URL'] + '/' + \
                out_folder + '/' + slug + '.html'

            content = self.transform_content(content)

            self.write_metadata(os.path.join(self.output_folder, out_folder,
                                             slug + '.meta'),
                                title, slug, post_date, description, tags)
            self.write_content(
                os.path.join(self.output_folder, out_folder, slug + '.wp'),
                content)
        else:
            print('Not going to import "{0}" because it seems to contain'
                  ' no content.'.format(title))

    def process_item(self, item):
        # The namespace usually is something like:
        # http://wordpress.org/export/1.2/
        wordpress_namespace = item.nsmap['wp']
        post_type = get_text_tag(
            item, '{{{0}}}post_type'.format(wordpress_namespace), 'post')

        if post_type == 'attachment':
            self.import_attachment(item, wordpress_namespace)
        elif post_type == 'post':
            self.import_item(item, wordpress_namespace, 'posts')
        else:
            self.import_item(item, wordpress_namespace, 'stories')

    def import_posts(self, channel):
        for item in channel.findall('item'):
            self.process_item(item)


def get_text_tag(tag, name, default):
    if tag is None:
        return default
    t = tag.find(name)
    if t is not None:
        return t.text
    else:
        return default
