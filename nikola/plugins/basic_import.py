# -*- coding: utf-8 -*-

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

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # NOQA

from lxml import etree, html
from mako.template import Template

from nikola import utils

links = {}


class ImportMixin(object):
    """Mixin with common used methods."""

    name = "import_mixin"
    needs_config = False
    doc_usage = "[options] wordpress_export_file"
    doc_purpose = "Import a wordpress dump."
    cmd_options = [
        {
            'name': 'output_folder',
            'long': 'output-folder',
            'short': 'o',
            'default': 'new_site',
            'help': 'Location to write imported content.'
        },
    ]

    def _execute(self, options={}, args=[]):
        """Import a blog from an export into a Nikola site."""
        raise NotImplementedError("Must be implemented by a subclass.")

    @classmethod
    def get_channel_from_file(cls, filename):
        tree = etree.fromstring(cls.read_xml_file(filename))
        channel = tree.find('channel')
        return channel

    @staticmethod
    def configure_redirections(url_map):
        redirections = []
        for k, v in url_map.items():
            if not k[-1] == '/':
                k = k + '/'

            # remove the initial "/" because src is a relative file path
            src = (urlparse(k).path + 'index.html')[1:]
            dst = (urlparse(v).path)
            if src == 'index.html':
                print("Can't do a redirect for: {0!r}".format(k))
            else:
                redirections.append((src, dst))

        return redirections

    def generate_base_site(self):
        if not os.path.exists(self.output_folder):
            os.system('nikola init ' + self.output_folder)
        else:
            self.import_into_existing_site = True
            print('The folder {0} already exists - assuming that this is a '
                  'already existing nikola site.'.format(self.output_folder))

        conf_template = Template(filename=os.path.join(
            os.path.dirname(utils.__file__), 'conf.py.in'))

        return conf_template

    @staticmethod
    def populate_context(channel):
        raise NotImplementedError("Must be implemented by a subclass.")

    @classmethod
    def transform_content(cls, content):
        return content

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
            fd.write('{0}\n'.format(title))
            fd.write('{0}\n'.format(slug))
            fd.write('{0}\n'.format(post_date))
            fd.write('{0}\n'.format(','.join(tags)))
            fd.write('\n')
            fd.write('{0}\n'.format(description))

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
            filename = 'conf.py.{name}-{time}'.format(
                time=datetime.datetime.now().strftime('%Y%m%d_%H%M%s'),
                name=self.name)
        config_output_path = os.path.join(self.output_folder, filename)
        print('Configuration will be written to:', config_output_path)

        return config_output_path

    @staticmethod
    def write_configuration(filename, rendered_template):
        with codecs.open(filename, 'w+', 'utf8') as fd:
            fd.write(rendered_template)


def replacer(dst):
    return links.get(dst, dst)
