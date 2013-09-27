# -*- coding: utf-8 -*-

# Copyright © 2012-2013 Roberto Alsina and others.

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

from __future__ import print_function
import os
import json
import shutil
from io import BytesIO

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils


class CommandInstallTheme(Command):
    """Install a theme."""

    name = "install_theme"
    doc_usage = "[[-u] theme_name] | [[-u] -l]"
    doc_purpose = "install theme into current site"
    output_dir = 'themes'
    cmd_options = [
        {
            'name': 'list',
            'short': 'l',
            'long': 'list',
            'type': bool,
            'default': False,
            'help': 'Show list of available themes.'
        },
        {
            'name': 'url',
            'short': 'u',
            'long': 'url',
            'type': str,
            'help': "URL for the theme repository (default: "
                    "http://themes.getnikola.com/v6/themes.json)",
            'default': 'http://themes.getnikola.com/v6/themes.json'
        },
    ]

    def _execute(self, options, args):
        """Install theme into current site."""
        if requests is None:
            utils.LOGGER.error('This command requires the requests package be installed.')
            return False

        listing = options['list']
        url = options['url']
        if args:
            name = args[0]
        else:
            name = None

        if name is None and not listing:
            utils.LOGGER.error("This command needs either a theme name or the -l option.")
            return False
        data = requests.get(url).text
        data = json.loads(data)
        if listing:
            print("Themes:")
            print("-------")
            for theme in sorted(data.keys()):
                print(theme)
            return True
        else:
            self.do_install(name, data)
        # See if the theme's parent is available. If not, install it
        while True:
            parent_name = utils.get_parent_theme_name(name)
            if parent_name is None:
                break
            try:
                utils.get_theme_path(parent_name)
                break
            except:  # Not available
                self.do_install(parent_name, data)
                name = parent_name

    def do_install(self, name, data):
        if name in data:
            utils.makedirs(self.output_dir)
            utils.LOGGER.notice('Downloading: ' + data[name])
            zip_file = BytesIO()
            zip_file.write(requests.get(data[name]).content)
            utils.LOGGER.notice('Extracting: {0} into themes'.format(name))
            utils.extract_all(zip_file)
        else:
            try:
                theme_path = utils.get_theme_path(name)
            except:
                utils.LOGGER.error("Can't find theme " + name)
                return False

            utils.makedirs(self.output_dir)
            dest_path = os.path.join(self.output_dir, name)
            if os.path.exists(dest_path):
                utils.LOGGER.error("{0} is already installed".format(name))
                return False

            utils.LOGGER.notice('Copying {0} into themes'.format(theme_path))
            shutil.copytree(theme_path, dest_path)
            return True
