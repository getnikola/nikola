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
import os
import re
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from lxml import etree, html, builder
from mako.template import Template

try:
    import requests
except ImportError:
    requests = None

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

    @staticmethod
    def generate_base_site(context):
        os.system('nikola init new_site')
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
        with open(dst_path, 'wb+') as fd:
            fd.write(requests.get(url).content)

    def import_attachment(self, item, wordpress_namespace):
        url = get_text_tag(item, '{%s}attachment_url' % wordpress_namespace, 'foo')
        link = get_text_tag(item, '{%s}link' % wordpress_namespace, 'foo')
        path = urlparse(url).path
        dst_path = os.path.join(*(['new_site', 'files']
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
    def write_content(filename, content):
        with open(filename, "wb+") as fd:
            if content.strip():
                # Handle sourcecode pseudo-tags
                content = re.sub('\[sourcecode language="([^"]+)"\]',
                                 "\n~~~~~~~~~~~~{.\\1}\n", content)
                content = content.replace('[/sourcecode]', "\n~~~~~~~~~~~~\n")
                doc = html.document_fromstring(content)
                doc.rewrite_links(replacer)
                # Replace H1 elements with H2 elements
                for tag in doc.findall('.//h1'):
                    if not tag.text:
                        print("Failed to fix bad title: %r" %
                              html.tostring(tag))
                    else:
                        tag.getparent().replace(tag, builder.E.h2(tag.text))
                fd.write(html.tostring(doc, encoding='utf8'))

    @staticmethod
    def write_metadata(filename, title, slug, post_date, description, tags):
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
            slug = get_text_tag(item, '{%s}post_name' % wordpress_namespace, None)
        if not slug:  # it *may* happen
            slug = get_text_tag(item, '{%s}post_id' % wordpress_namespace, None)
        if not slug:  # should never happen
            print("Error converting post:", title)
            return

        description = get_text_tag(item, 'description', '')
        post_date = get_text_tag(item, '{%s}post_date' % wordpress_namespace, None)
        status = get_text_tag(item, '{%s}status' % wordpress_namespace, 'publish')
        content = get_text_tag(
            item, '{http://purl.org/rss/1.0/modules/content/}encoded', '')

        tags = []
        if status != 'publish':
            tags.append('draft')
        for tag in item.findall('category'):
            text = tag.text
            if text == 'Uncategorized':
                continue
            tags.append(text)

        self.url_map[link] = self.context['BLOG_URL'] + '/' + \
            out_folder + '/' + slug + '.html'

        self.write_metadata(os.path.join('new_site', out_folder,
                                         slug + '.meta'),
                            title, slug, post_date, description, tags)
        self.write_content(
            os.path.join('new_site', out_folder, slug + '.wp'), content)

    def process_item(self, item):
        # The namespace usually is something like:
        # http://wordpress.org/export/1.2/
        wordpress_namespace = item.nsmap['wp']
        post_type = get_text_tag(item, '{%s}post_type' % wordpress_namespace, 'post')

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

    @staticmethod
    def write_configuration(filename, rendered_template):
        with codecs.open(filename, 'w+', 'utf8') as fd:
            fd.write(rendered_template)

    def run(self, fname=None):
        # Parse the data
        if requests is None:
            print('To use the import_wordpress command, you have to install the "requests" package.')
            return
        if fname is None:
            print("Usage: nikola import_wordpress wordpress_dump.xml")
            return

        self.url_map = {}
        channel = self.get_channel_from_file(fname)
        self.context = self.populate_context(channel)
        conf_template = self.generate_base_site(self.context)
        self.context['REDIRECTIONS'] = self.configure_redirections(
            self.url_map)

        self.import_posts(channel)
        self.write_urlmap_csv(
            os.path.join('new_site', 'url_map.csv'), self.url_map)
        self.write_configuration(os.path.join(
            'new_site', 'conf.py'), conf_template.render(**self.context))


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
