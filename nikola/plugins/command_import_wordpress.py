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
import codecs
import csv
import datetime
import os
import re
from optparse import OptionParser

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # NOQA

from lxml import etree, html
from mako.template import Template

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils

links = {}


class CommandImportWordpress(Command):
    """Import a wordpress dump."""

    name = "import_wordpress"

    @staticmethod
    def read_xml_file(filename):
        xml = []

        with open(filename, 'rb') as fd:
            for line in fd:
                # These explode etree and are useless
                if b'<atom:link rel=' in line:
                    continue
                xml.append(line)
            xml = b'\n'.join(xml)

        return xml

    @classmethod
    def get_channel_from_file(cls, filename):
        tree = etree.fromstring(cls.read_xml_file(filename))
        channel = tree.find('channel')
        return channel

    @staticmethod
    def configure_redirections(url_map):
        redirections = []
        for k, v in url_map.items():
            # remove the initial "/" because src is a relative file path
            src = (urlparse(k).path + 'index.html')[1:]
            dst = (urlparse(v).path)
            if src == 'index.html':
                print("Can't do a redirect for: %r" % k)
            else:
                redirections.append((src, dst))

        return redirections

    def generate_base_site(self):
        if not os.path.exists(self.output_folder):
            os.system('nikola init --empty %s' % (self.output_folder, ))
        else:
            self.import_into_existing_site = True
            print('The folder %s already exists - assuming that this is a '
                  'already existing nikola site.' % self.output_folder)

        conf_template = Template(filename=os.path.join(
            os.path.dirname(utils.__file__), 'conf.py.in'))

        return conf_template

    @staticmethod
    def populate_context(channel):
        wordpress_namespace = channel.nsmap['wp']

        context = {}
        context['DEFAULT_LANG'] = get_text_tag(channel, 'language', 'en')[:2]
        context['BLOG_TITLE'] = get_text_tag(channel, 'title',
                                             'PUT TITLE HERE')
        context['BLOG_DESCRIPTION'] = get_text_tag(
            channel, 'description', 'PUT DESCRIPTION HERE')
        context['BLOG_URL'] = get_text_tag(channel, 'link', '#')
        author = channel.find('{%s}author' % wordpress_namespace)
        context['BLOG_EMAIL'] = get_text_tag(
            author,
            '{%s}author_email' % wordpress_namespace,
            "joe@example.com")
        context['BLOG_AUTHOR'] = get_text_tag(
            author,
            '{%s}author_display_name' % wordpress_namespace,
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

    @staticmethod
    def download_url_content_to_file(url, dst_path):
        try:
            with open(dst_path, 'wb+') as fd:
                fd.write(requests.get(url).content)
        except requests.exceptions.ConnectionError as err:
            print("Downloading %s to %s failed: %s" % (url, dst_path, err))

    def import_attachment(self, item, wordpress_namespace):
        url = get_text_tag(
            item, '{%s}attachment_url' % wordpress_namespace, 'foo')
        link = get_text_tag(item, '{%s}link' % wordpress_namespace, 'foo')
        path = urlparse(url).path
        dst_path = os.path.join(*([self.output_folder, 'files']
                                  + list(path.split('/'))))
        dst_dir = os.path.dirname(dst_path)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        print("Downloading %s => %s" % (url, dst_path))
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

    @classmethod
    def transform_content(cls, content):
        new_content = cls.transform_sourcecode(content)
        return cls.transform_caption(new_content)

    @classmethod
    def write_content(cls, filename, content):
        doc = html.document_fromstring(content)
        doc.rewrite_links(replacer)

        with open(filename, "wb+") as fd:
            fd.write(html.tostring(doc, encoding='utf8'))

    @staticmethod
    def write_metadata(filename, title, slug, post_date, description, tags):
        if not description:
            description = ""

        with codecs.open(filename, "w+", "utf8") as fd:
            fd.write('%s\n' % title)
            fd.write('%s\n' % slug)
            fd.write('%s\n' % post_date)
            fd.write('%s\n' % ','.join(tags))
            fd.write('\n')
            fd.write('%s\n' % description)

    def import_item(self, item, wordpress_namespace, out_folder=None):
        """Takes an item from the feed and creates a post file."""
        if out_folder is None:
            out_folder = 'posts'

        title = get_text_tag(item, 'title', 'NO TITLE')
        # link is something like http://foo.com/2012/09/01/hello-world/
        # So, take the path, utils.slugify it, and that's our slug
        link = get_text_tag(item, 'link', None)
        slug = utils.slugify(urlparse(link).path)
        if not slug:  # it happens if the post has no "nice" URL
            slug = get_text_tag(
                item, '{%s}post_name' % wordpress_namespace, None)
        if not slug:  # it *may* happen
            slug = get_text_tag(
                item, '{%s}post_id' % wordpress_namespace, None)
        if not slug:  # should never happen
            print("Error converting post:", title)
            return

        description = get_text_tag(item, 'description', '')
        post_date = get_text_tag(
            item, '{%s}post_date' % wordpress_namespace, None)
        status = get_text_tag(
            item, '{%s}status' % wordpress_namespace, 'publish')
        content = get_text_tag(
            item, '{http://purl.org/rss/1.0/modules/content/}encoded', '')

        tags = []
        if status != 'publish':
            tags.append('draft')
            is_draft = True
        else:
            is_draft = False

        for tag in item.findall('category'):
            text = tag.text
            if text == 'Uncategorized':
                continue
            tags.append(text)

        self.url_map[link] = self.context['BLOG_URL'] + '/' + \
            out_folder + '/' + slug + '.html'

        if is_draft and self.exclude_drafts:
            print('Draft "%s" will not be imported.' % (title, ))
        elif content.strip():
            # If no content is found, no files are written.
            content = self.transform_content(content)

            self.write_metadata(os.path.join(self.output_folder, out_folder,
                                             slug + '.meta'),
                                title, slug, post_date, description, tags)
            self.write_content(
                os.path.join(self.output_folder, out_folder, slug + '.wp'),
                content)
        else:
            print('Not going to import "%s" because it seems to contain'
                  ' no content.' % (title, ))

    def process_item(self, item):
        # The namespace usually is something like:
        # http://wordpress.org/export/1.2/
        wordpress_namespace = item.nsmap['wp']
        post_type = get_text_tag(
            item, '{%s}post_type' % wordpress_namespace, 'post')

        if post_type == 'attachment':
            self.import_attachment(item, wordpress_namespace)
        elif post_type == 'post':
            self.import_item(item, wordpress_namespace, 'posts')
        else:
            self.import_item(item, wordpress_namespace, 'stories')

    def import_posts(self, channel):
        for item in channel.findall('item'):
            self.process_item(item)

    @staticmethod
    def write_urlmap_csv(output_file, url_map):
        with codecs.open(output_file, 'w+', 'utf8') as fd:
            csv_writer = csv.writer(fd)
            for item in url_map.items():
                csv_writer.writerow(item)

    def get_configuration_output_path(self):
        if not self.import_into_existing_site:
            filename = 'conf.py'
        else:
            filename = 'conf.py.wordpress_import-%s' % datetime.datetime.now(
            ).strftime('%Y%m%d_%H%M%s')
        config_output_path = os.path.join(self.output_folder, filename)
        print('Configuration will be written to: %s' % config_output_path)

        return config_output_path

    @staticmethod
    def write_configuration(filename, rendered_template):
        with codecs.open(filename, 'w+', 'utf8') as fd:
            fd.write(rendered_template)

    def run(self, *arguments):
        """Import a Wordpress blog from an export file into a Nikola site."""
        # Parse the data
        if requests is None:
            print('To use the import_wordpress command,'
                  ' you have to install the "requests" package.')
            return

        parser = OptionParser(usage="nikola %s [options] "
                              "wordpress_export_file" % self.name)
        parser.add_option('-f', '--filename', dest='filename',
                          help='WordPress export file from which the import '
                          'made.')
        parser.add_option('-o', '--output-folder', dest='output_folder',
                          default='new_site', help='The location into which '
                          'the imported content will be written')
        parser.add_option('-d', '--no-drafts', dest='exclude_drafts',
                          default=False, action="store_true", help='Do not '
                          'import drafts.')

        (options, args) = parser.parse_args(list(arguments))

        if not options.filename and args:
            options.filename = args[0]

        if not options.filename:
            parser.print_usage()
            return

        self.wordpress_export_file = options.filename
        self.output_folder = options.output_folder
        self.import_into_existing_site = False
        self.exclude_drafts = options.exclude_drafts
        self.url_map = {}
        channel = self.get_channel_from_file(self.wordpress_export_file)
        self.context = self.populate_context(channel)
        conf_template = self.generate_base_site()
        self.context['REDIRECTIONS'] = self.configure_redirections(
            self.url_map)

        self.import_posts(channel)
        self.write_urlmap_csv(
            os.path.join(self.output_folder, 'url_map.csv'), self.url_map)

        self.write_configuration(self.get_configuration_output_path(
        ), conf_template.render(**self.context))


def replacer(dst):
    return links.get(dst, dst)


def get_text_tag(tag, name, default):
    if tag is None:
        return default
    t = tag.find(name)
    if t is not None:
        return t.text
    else:
        return default
