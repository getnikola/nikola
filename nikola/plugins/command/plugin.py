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

from __future__ import print_function
import io
import os
import shutil
import subprocess
import sys
import requests

import pygments
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

from nikola.plugin_categories import Command
from nikola import utils

LOGGER = utils.get_logger('plugin', utils.STDERR_HANDLER)


# Stolen from textwrap in Python 3.3.2.
def indent(text, prefix, predicate=None):  # NOQA
    """Adds 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    """
    if predicate is None:
        def predicate(line):
            return line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if predicate(line) else line)
    return ''.join(prefixed_lines())


class CommandPlugin(Command):
    """Manage plugins."""

    json = None
    name = "plugin"
    doc_usage = "[[-u][--user] --install name] | [[-u] [-l |--upgrade|--list-installed] | [--uninstall name]]"
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
        command_count = [bool(x) for x in (
            install,
            uninstall,
            upgrade,
            list_available,
            list_installed)].count(True)
        if command_count > 1 or command_count == 0:
            print(self.help())
            return

        if not self.site.configured and not user_mode and install:
            LOGGER.notice('No site found, assuming --user')
            user_mode = True

        if user_mode:
            self.output_dir = os.path.expanduser('~/.nikola/plugins')
        else:
            self.output_dir = 'plugins'

        if list_available:
            self.list_available(url)
        elif list_installed:
            self.list_installed()
        elif upgrade:
            self.do_upgrade(url)
        elif uninstall:
            self.do_uninstall(uninstall)
        elif install:
            self.do_install(url, install)

    def list_available(self, url):
        data = self.get_json(url)
        print("Available Plugins:")
        print("------------------")
        for plugin in sorted(data.keys()):
            print(plugin)
        return True

    def list_installed(self):
        plugins = []
        for plugin in self.site.plugin_manager.getAllPlugins():
            p = plugin.path
            if os.path.isdir(p):
                p = p + os.sep
            else:
                p = p + '.py'
            plugins.append([plugin.name, p])

        plugins.sort()
        for name, path in plugins:
            print('{0} at {1}'.format(name, path))

    def do_upgrade(self, url):
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
                    return False
                else:
                    path = tail
            self.do_install(url, name)

    def do_install(self, url, name):
        data = self.get_json(url)
        if name in data:
            utils.makedirs(self.output_dir)
            LOGGER.info('Downloading: ' + data[name])
            zip_file = io.BytesIO()
            zip_file.write(requests.get(data[name]).content)
            LOGGER.info('Extracting: {0} into {1}/'.format(name, self.output_dir))
            utils.extract_all(zip_file, self.output_dir)
            dest_path = os.path.join(self.output_dir, name)
        else:
            try:
                plugin_path = utils.get_plugin_path(name)
            except:
                LOGGER.error("Can't find plugin " + name)
                return False

            utils.makedirs(self.output_dir)
            dest_path = os.path.join(self.output_dir, name)
            if os.path.exists(dest_path):
                LOGGER.error("{0} is already installed".format(name))
                return False

            LOGGER.info('Copying {0} into plugins'.format(plugin_path))
            shutil.copytree(plugin_path, dest_path)

        reqpath = os.path.join(dest_path, 'requirements.txt')
        if os.path.exists(reqpath):
            LOGGER.notice('This plugin has Python dependencies.')
            LOGGER.info('Installing dependencies with pip...')
            try:
                subprocess.check_call(('pip', 'install', '-r', reqpath))
            except subprocess.CalledProcessError:
                LOGGER.error('Could not install the dependencies.')
                print('Contents of the requirements.txt file:\n')
                with io.open(reqpath, 'r', encoding='utf-8') as fh:
                    print(indent(fh.read(), 4 * ' '))
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
                    print(indent(i.strip(), 4 * ' '))
                    print(indent(j.strip(), 8 * ' '))
                    print()

            print('You have to install those yourself or through a package '
                  'manager.')
        confpypath = os.path.join(dest_path, 'conf.py.sample')
        if os.path.exists(confpypath):
            LOGGER.notice('This plugin has a sample config file.  Integrate it with yours in order to make this plugin work!')
            print('Contents of the conf.py.sample file:\n')
            with io.open(confpypath, 'r', encoding='utf-8') as fh:
                if self.site.colorful:
                    print(indent(pygments.highlight(
                        fh.read(), PythonLexer(), TerminalFormatter()),
                        4 * ' '))
                else:
                    print(indent(fh.read(), 4 * ' '))
        return True

    def do_uninstall(self, name):
        for plugin in self.site.plugin_manager.getAllPlugins():  # FIXME: this is repeated thrice
            p = plugin.path
            if os.path.isdir(p):
                p = p + os.sep
            else:
                p = os.path.dirname(p)
            if name == plugin.name:  # Uninstall this one
                LOGGER.warning('About to uninstall plugin: {0}'.format(name))
                LOGGER.warning('This will delete {0}'.format(p))
                inpf = raw_input if sys.version_info[0] == 2 else input
                sure = inpf('Are you sure? [y/n] ')
                if sure.lower().startswith('y'):
                    LOGGER.warning('Removing {0}'.format(p))
                    shutil.rmtree(p)
                return True
        LOGGER.error('Unknown plugin: {0}'.format(name))
        return False

    def get_json(self, url):
        if self.json is None:
            self.json = requests.get(url).json()
        return self.json
