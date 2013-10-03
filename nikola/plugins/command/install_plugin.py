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
import codecs
import os
import json
import shutil
import subprocess
from io import BytesIO

import pygments
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils


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


class CommandInstallPlugin(Command):
    """Install a plugin."""

    name = "install_plugin"
    doc_usage = "[[-u] plugin_name] | [[-u] -l]"
    doc_purpose = "install plugin into current site"
    output_dir = 'plugins'
    cmd_options = [
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
                    "http://plugins.getnikola.com/v6/plugins.json)",
            'default': 'http://plugins.getnikola.com/v6/plugins.json'
        },
    ]

    def _execute(self, options, args):
        """Install plugin into current site."""
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
            utils.LOGGER.error("This command needs either a plugin name or the -l option.")
            return False
        data = requests.get(url).text
        data = json.loads(data)
        if listing:
            print("Plugins:")
            print("--------")
            for plugin in sorted(data.keys()):
                print(plugin)
            return True
        else:
            self.do_install(name, data)

    def do_install(self, name, data):
        if name in data:
            utils.makedirs(self.output_dir)
            utils.LOGGER.notice('Downloading: ' + data[name])
            zip_file = BytesIO()
            zip_file.write(requests.get(data[name]).content)
            utils.LOGGER.notice('Extracting: {0} into plugins'.format(name))
            utils.extract_all(zip_file, 'plugins')
            dest_path = os.path.join('plugins', name)
        else:
            try:
                plugin_path = utils.get_plugin_path(name)
            except:
                utils.LOGGER.error("Can't find plugin " + name)
                return False

            utils.makedirs(self.output_dir)
            dest_path = os.path.join(self.output_dir, name)
            if os.path.exists(dest_path):
                utils.LOGGER.error("{0} is already installed".format(name))
                return False

            utils.LOGGER.notice('Copying {0} into plugins'.format(plugin_path))
            shutil.copytree(plugin_path, dest_path)

        reqpath = os.path.join(dest_path, 'requirements.txt')
        print(reqpath)
        if os.path.exists(reqpath):
            utils.LOGGER.notice('This plugin has Python dependencies.')
            utils.LOGGER.notice('Installing dependencies with pip...')
            try:
                subprocess.check_call(('pip', 'install', '-r', reqpath))
            except subprocess.CalledProcessError:
                utils.LOGGER.error('Could not install the dependencies.')
                print('Contents of the requirements.txt file:\n')
                with codecs.open(reqpath, 'rb', 'utf-8') as fh:
                    print(indent(fh.read(), 4 * ' '))
                print('You have to install those yourself or through a '
                      'package manager.')
            else:
                utils.LOGGER.notice('Dependency installation succeeded.')
        reqnpypath = os.path.join(dest_path, 'requirements-nonpy.txt')
        if os.path.exists(reqnpypath):
            utils.LOGGER.notice('This plugin has third-party '
                                'dependencies you need to install '
                                'manually.')
            print('Contents of the requirements-nonpy.txt file:\n')
            with codecs.open(reqnpypath, 'rb', 'utf-8') as fh:
                for l in fh.readlines():
                    i, j = l.split('::')
                    print(indent(i.strip(), 4 * ' '))
                    print(indent(j.strip(), 8 * ' '))
                    print()

            print('You have to install those yourself or through a package '
                  'manager.')
        confpypath = os.path.join(dest_path, 'conf.py.sample')
        if os.path.exists(confpypath):
            utils.LOGGER.notice('This plugin has a sample config file.')
            print('Contents of the conf.py.sample file:\n')
            with codecs.open(confpypath, 'rb', 'utf-8') as fh:
                print(indent(pygments.highlight(
                    fh.read(), PythonLexer(), TerminalFormatter()), 4 * ' '))
        return True
