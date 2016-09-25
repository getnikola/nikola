# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Manage plugins."""

from __future__ import print_function
import io
import os
import sys
import shutil
import subprocess
import time
import requests

import pygments
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

from nikola.plugin_categories import Command
from nikola import utils

LOGGER = utils.get_logger('plugin', utils.STDERR_HANDLER)


class CommandPlugin(Command):
    """Manage plugins."""

    json = None
    name = "plugin"
    doc_usage = "[-u url] [--user] [-i name] [-r name] [--upgrade] [-l] [--list-installed]"
    doc_purpose = "manage plugins"
    output_dir = None
    needs_config = False
    cmd_options = [
        {
            'name': 'install',
            'short': 'i',
            'long': 'install',
            'type': str,
            'default': '',
            'help': 'Install a plugin.',
        },
        {
            'name': 'uninstall',
            'long': 'uninstall',
            'short': 'r',
            'type': str,
            'default': '',
            'help': 'Uninstall a plugin.'
        },
        {
            'name': 'list',
            'short': 'l',
            'long': 'list',
            'type': bool,
            'default': False,
            'help': 'Show list of available plugins.'
        },
        {
            'name': 'url',
            'short': 'u',
            'long': 'url',
            'type': str,
            'help': "URL for the plugin repository (default: "
                    "https://plugins.getnikola.com/v7/plugins.json)",
            'default': 'https://plugins.getnikola.com/v7/plugins.json'
        },
        {
            'name': 'user',
            'long': 'user',
            'type': bool,
            'help': "Install user-wide, available for all sites.",
            'default': False
        },
        {
            'name': 'upgrade',
            'long': 'upgrade',
            'type': bool,
            'help': "Upgrade all installed plugins.",
            'default': False
        },
        {
            'name': 'list_installed',
            'long': 'list-installed',
            'type': bool,
            'help': "List the installed plugins with their location.",
            'default': False
        },
    ]

    def _execute(self, options, args):
        """Install plugin into current site."""
        url = options['url']
        user_mode = options['user']

        # See the "mode" we need to operate in
        install = options.get('install')
        uninstall = options.get('uninstall')
        upgrade = options.get('upgrade')
        list_available = options.get('list')
        list_installed = options.get('list_installed')
        show_install_notes = options.get('show_install_notes', True)
        command_count = [bool(x) for x in (
            install,
            uninstall,
            upgrade,
            list_available,
            list_installed)].count(True)
        if command_count > 1 or command_count == 0:
            print(self.help())
            return 2

        if options.get('output_dir') is not None:
            self.output_dir = options.get('output_dir')
        else:
            if not self.site.configured and not user_mode and install:
                LOGGER.notice('No site found, assuming --user')
                user_mode = True

            if user_mode:
                self.output_dir = os.path.expanduser('~/.nikola/plugins')
            else:
                self.output_dir = 'plugins'

        if list_available:
            return self.list_available(url)
        elif list_installed:
            return self.list_installed()
        elif upgrade:
            return self.do_upgrade(url)
        elif uninstall:
            return self.do_uninstall(uninstall)
        elif install:
            return self.do_install(url, install, show_install_notes)

    def list_available(self, url):
        """List all available plugins."""
        data = self.get_json(url)
        print("Available Plugins:")
        print("------------------")
        for plugin in sorted(data.keys()):
            print(plugin)
        return 0

    def list_installed(self):
        """List installed plugins."""
        plugins = []
        for plugin in self.site.plugin_manager.getAllPlugins():
            p = plugin.path
            if os.path.isdir(p):
                p = p + os.sep
            else:
                p = p + '.py'
            plugins.append([plugin.name, p])

        plugins.sort()
        print('Installed Plugins:')
        print('------------------')
        for name, path in plugins:
            print('{0} at {1}'.format(name, path))
        print('\n\nAlso, you have disabled these plugins: {}'.format(self.site.config['DISABLED_PLUGINS']))
        return 0

    def do_upgrade(self, url):
        """Upgrade all installed plugins."""
        LOGGER.warning('This is not very smart, it just reinstalls some plugins and hopes for the best')
        data = self.get_json(url)
        plugins = []
        for plugin in self.site.plugin_manager.getAllPlugins():
            p = plugin.path
            if os.path.isdir(p):
                p = p + os.sep
            else:
                p = p + '.py'
            if plugin.name in data:
                plugins.append([plugin.name, p])
        print('Will upgrade {0} plugins: {1}'.format(len(plugins), ', '.join(n for n, _ in plugins)))
        for name, path in plugins:
            print('Upgrading {0}'.format(name))
            p = path
            while True:
                tail, head = os.path.split(path)
                if head == 'plugins':
                    self.output_dir = path
                    break
                elif tail == '':
                    LOGGER.error("Can't find the plugins folder for path: {0}".format(p))
                    return 1
                else:
                    path = tail
            self.do_install(url, name)
        return 0

    def do_install(self, url, name, show_install_notes=True):
        """Download and install a plugin."""
        data = self.get_json(url)
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
            LOGGER.info('Extracting: {0} into {1}/'.format(name, self.output_dir))
            utils.extract_all(zip_file, self.output_dir)
            dest_path = os.path.join(self.output_dir, name)
        else:
            try:
                plugin_path = utils.get_plugin_path(name)
            except:
                LOGGER.error("Can't find plugin " + name)
                return 1

            utils.makedirs(self.output_dir)
            dest_path = os.path.join(self.output_dir, name)
            if os.path.exists(dest_path):
                LOGGER.error("{0} is already installed".format(name))
                return 1

            LOGGER.info('Copying {0} into plugins'.format(plugin_path))
            shutil.copytree(plugin_path, dest_path)

        reqpath = os.path.join(dest_path, 'requirements.txt')
        if os.path.exists(reqpath):
            LOGGER.notice('This plugin has Python dependencies.')
            LOGGER.info('Installing dependencies with pip...')
            try:
                subprocess.check_call((sys.executable, '-m', 'pip', 'install', '-r', reqpath))
            except subprocess.CalledProcessError:
                LOGGER.error('Could not install the dependencies.')
                print('Contents of the requirements.txt file:\n')
                with io.open(reqpath, 'r', encoding='utf-8') as fh:
                    print(utils.indent(fh.read(), 4 * ' '))
                print('You have to install those yourself or through a '
                      'package manager.')
            else:
                LOGGER.info('Dependency installation succeeded.')
        reqnpypath = os.path.join(dest_path, 'requirements-nonpy.txt')
        if os.path.exists(reqnpypath):
            LOGGER.notice('This plugin has third-party '
                          'dependencies you need to install '
                          'manually.')
            print('Contents of the requirements-nonpy.txt file:\n')
            with io.open(reqnpypath, 'r', encoding='utf-8') as fh:
                for l in fh.readlines():
                    i, j = l.split('::')
                    print(utils.indent(i.strip(), 4 * ' '))
                    print(utils.indent(j.strip(), 8 * ' '))
                    print()

            print('You have to install those yourself or through a package '
                  'manager.')
        confpypath = os.path.join(dest_path, 'conf.py.sample')
        if os.path.exists(confpypath) and show_install_notes:
            LOGGER.notice('This plugin has a sample config file.  Integrate it with yours in order to make this plugin work!')
            print('Contents of the conf.py.sample file:\n')
            with io.open(confpypath, 'r', encoding='utf-8') as fh:
                if self.site.colorful:
                    print(utils.indent(pygments.highlight(
                        fh.read(), PythonLexer(), TerminalFormatter()),
                        4 * ' '))
                else:
                    print(utils.indent(fh.read(), 4 * ' '))
        return 0

    def do_uninstall(self, name):
        """Uninstall a plugin."""
        for plugin in self.site.plugin_manager.getAllPlugins():  # FIXME: this is repeated thrice
            if name == plugin.name:  # Uninstall this one
                p = plugin.path
                if os.path.isdir(p):
                    # Plugins that have a package in them need to delete parent
                    # Issue #2356
                    p = p + os.sep
                    p = os.path.abspath(os.path.join(p, os.pardir))
                else:
                    p = os.path.dirname(p)
                LOGGER.warning('About to uninstall plugin: {0}'.format(name))
                LOGGER.warning('This will delete {0}'.format(p))
                sure = utils.ask_yesno('Are you sure?')
                if sure:
                    LOGGER.warning('Removing {0}'.format(p))
                    shutil.rmtree(p)
                    return 0
                return 1
        LOGGER.error('Unknown plugin: {0}'.format(name))
        return 1

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
