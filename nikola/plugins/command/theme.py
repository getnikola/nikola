# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina, Chris Warrick and others.

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

"""Manage themes."""

from __future__ import print_function
import os
import io
import shutil
import time
import requests

import pygments
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

from nikola.plugin_categories import Command
from nikola import utils

LOGGER = utils.get_logger('theme', utils.STDERR_HANDLER)


class CommandTheme(Command):
    """Manage themes."""

    json = None
    name = "theme"
    doc_usage = "[-u] [-i theme_name] [-l] [-g] [-n] [-c]"
    doc_purpose = "manage themes"
    output_dir = 'themes'
    cmd_options = [
        {
            'name': 'install',
            'short': 'i',
            'long': 'install',
            'type': str,
            'default': '',
            'help': 'Install a theme.'
        },
        {
            'name': 'uninstall',
            'long': 'uninstall',
            'short': 'r',
            'type': str,
            'default': '',
            'help': 'Uninstall a theme.'
        },
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
                    "https://themes.getnikola.com/v7/themes.json)",
            'default': 'https://themes.getnikola.com/v7/themes.json'
        },
        {
            'name': 'getpath',
            'short': 'g',
            'long': 'get-path',
            'type': str,
            'default': '',
            'help': "Print the path for installed theme",
        },
    ]

    def _execute(self, options, args):
        """Install theme into current site."""
        url = options['url']

        # See the "mode" we need to operate in
        install = options.get('install')
        uninstall = options.get('uninstall')
        list_available = options.get('list')
        get_path = options.get('getpath')
        command_count = [bool(x) for x in (
            install,
            uninstall,
            list_available,
            get_path)].count(True)
        if command_count > 1 or command_count == 0:
            print(self.help())
            return 2

        if list_available:
            return self.list_available(url)
        elif uninstall:
            return self.do_uninstall(uninstall)
        elif install:
            return self.do_install_deps(url, install)
        elif get_path:
            return self.get_path(get_path)

    def do_install_deps(self, url, name):
        """Install themes and their dependencies."""
        data = self.get_json(url)
        # `name` may be modified by the while loop.
        origname = name
        installstatus = self.do_install(name, data)
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
        if installstatus:
            LOGGER.notice('Remember to set THEME="{0}" in conf.py to use this theme.'.format(origname))

    def do_install(self, name, data):
        """Download and install a theme."""
        if name in data:
            utils.makedirs(self.output_dir)
            url = data[name]
            LOGGER.info("Downloading '{0}'".format(url))
            try:
                zip_data = requests.get(url).content
            except requests.exceptions.SSLError:
                LOGGER.warning("SSL error, using http instead of https (press ^C to abort)")
                time.sleep(1)
                url = url.replace('https', 'http', 1)
                zip_data = requests.get(url).content

            zip_file = io.BytesIO()
            zip_file.write(zip_data)
            LOGGER.info("Extracting '{0}' into themes/".format(name))
            utils.extract_all(zip_file)
            dest_path = os.path.join(self.output_dir, name)
        else:
            dest_path = os.path.join(self.output_dir, name)
            try:
                theme_path = utils.get_theme_path(name)
                LOGGER.error("Theme '{0}' is already installed in {1}".format(name, theme_path))
            except Exception:
                LOGGER.error("Can't find theme {0}".format(name))

            return False

        confpypath = os.path.join(dest_path, 'conf.py.sample')
        if os.path.exists(confpypath):
            LOGGER.notice('This theme has a sample config file.  Integrate it with yours in order to make this theme work!')
            print('Contents of the conf.py.sample file:\n')
            with io.open(confpypath, 'r', encoding='utf-8') as fh:
                if self.site.colorful:
                    print(utils.indent(pygments.highlight(
                        fh.read(), PythonLexer(), TerminalFormatter()),
                        4 * ' '))
                else:
                    print(utils.indent(fh.read(), 4 * ' '))
        return True

    def do_uninstall(self, name):
        """Uninstall a theme."""
        try:
            path = utils.get_theme_path(name)
        except Exception:
            LOGGER.error('Unknown theme: {0}'.format(name))
            return 1
        LOGGER.warning('About to uninstall plugin: {0}'.format(name))
        LOGGER.warning('This will delete {0}'.format(path))
        sure = utils.ask_yesno('Are you sure?')
        if sure:
            LOGGER.warning('Removing {0}'.format(path))
            shutil.rmtree(path)
            return 0
        return 1

    def get_path(self, name):
        """Get path for an installed theme."""
        try:
            path = utils.get_theme_path(name)
            print(path)
        except Exception:
            print("not installed")
        return 0

    def list_available(self, url):
        """List all available themes."""
        data = self.get_json(url)
        print("Available Themes:")
        print("-----------------")
        for theme in sorted(data.keys()):
            print(theme)
        return 0

    def get_json(self, url):
        """Download the JSON file with all plugins."""
        if self.json is None:
            try:
                self.json = requests.get(url).json()
            except requests.exceptions.SSLError:
                LOGGER.warning("SSL error, using http instead of https (press ^C to abort)")
                time.sleep(1)
                url = url.replace('https', 'http', 1)
                self.json = requests.get(url).json()
        return self.json
