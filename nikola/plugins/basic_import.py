# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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
import io
import csv
import datetime
import os
import sys
from pkg_resources import resource_filename

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
    doc_usage = "[options] export_file"
    doc_purpose = "import a dump from a different engine."
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
                utils.LOGGER.warn("Can't do a redirect for: {0!r}".format(k))
            else:
                redirections.append((src, dst))

        return redirections

    def generate_base_site(self):
        if not os.path.exists(self.output_folder):
            os.system('nikola init -q ' + self.output_folder)
        else:
            self.import_into_existing_site = True
            utils.LOGGER.notice('The folder {0} already exists - assuming that this is a '
                                'already existing Nikola site.'.format(self.output_folder))

        filename = resource_filename('nikola', 'conf.py.in')
        # The 'strict_undefined=True' will give the missing symbol name if any,
        # (ex: NameError: 'THEME' is not defined )
        # for other errors from mako/runtime.py, you can add format_extensions=True ,
        # then more info will be writen to *somefile* (most probably conf.py)
        conf_template = Template(filename=filename, strict_undefined=True)

        return conf_template

    @staticmethod
    def populate_context(channel):
        raise NotImplementedError("Must be implemented by a subclass.")

    @classmethod
    def transform_content(cls, content):
        return content

    @classmethod
    def write_content(cls, filename, content, rewrite_html=True):
        if rewrite_html:
            doc = html.document_fromstring(content)
            doc.rewrite_links(replacer)
            content = html.tostring(doc, encoding='utf8')
        else:
            content = content.encode('utf-8')

        utils.makedirs(os.path.dirname(filename))
        with open(filename, "wb+") as fd:
            fd.write(content)

    @staticmethod
    def write_metadata(filename, title, slug, post_date, description, tags, **kwargs):
        if not description:
            description = ""

        utils.makedirs(os.path.dirname(filename))
        with io.open(filename, "w+", encoding="utf8") as fd:
            data = {'title': title, 'slug': slug, 'date': post_date, 'tags': ','.join(tags), 'description': description}
            data.update(kwargs)
            fd.write(utils.write_metadata(data))

    @staticmethod
    def write_urlmap_csv(output_file, url_map):
        utils.makedirs(os.path.dirname(output_file))
        fmode = 'wb+' if sys.version_info[0] == 2 else 'w+'
        with io.open(output_file, fmode) as fd:
            csv_writer = csv.writer(fd)
            for item in url_map.items():
                csv_writer.writerow(item)

    def get_configuration_output_path(self):
        if not self.import_into_existing_site:
            filename = 'conf.py'
        else:
            filename = 'conf.py.{name}-{time}'.format(
                time=datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
                name=self.name)
        config_output_path = os.path.join(self.output_folder, filename)
        utils.LOGGER.info('Configuration will be written to: {0}'.format(config_output_path))

        return config_output_path

    @staticmethod
    def write_configuration(filename, rendered_template):
        utils.makedirs(os.path.dirname(filename))
        with io.open(filename, 'w+', encoding='utf8') as fd:
            fd.write(rendered_template)


def replacer(dst):
    return links.get(dst, dst)
