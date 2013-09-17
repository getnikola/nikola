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
import json
from io import BytesIO

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils


class CommandInstallTheme(Command):
    """Start test server."""

    name = "install_theme"
    doc_usage = "[[-u] theme_name] | [[-u] -l]"
    doc_purpose = "install theme into current site"
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
                    "http://themes.nikola.ralsina.com.ar/v6/themes.json)",
            'default': 'http://themes.nikola.ralsina.com.ar/v6/themes.json'
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
            if name in data:
                utils.makedirs('themes')
                utils.LOGGER.notice('Downloading: ' + data[name])
                zip_file = BytesIO()
                zip_file.write(requests.get(data[name]).content)
                utils.LOGGER.notice('Extracting: {0} into themes'.format(name))
                utils.extract_all(zip_file)
            else:
                utils.LOGGER.error("Can't find theme " + name)
                return False
