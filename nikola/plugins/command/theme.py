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
from pkg_resources import resource_filename

from nikola.plugin_categories import Command
from nikola import utils

LOGGER = utils.get_logger('theme', utils.STDERR_HANDLER)


class CommandTheme(Command):
    """Manage themes."""

    json = None
    name = "theme"
    doc_usage = "[-u url] [-i theme_name] [-r theme_name] [-l] [--list-installed] [-g] [-n theme_name] [-c template_name]"
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
            'name': 'list_installed',
            'long': 'list-installed',
            'type': bool,
            'help': "List the installed themes with their location.",
            'default': False
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
        {
            'name': 'copy-template',
            'short': 'c',
            'long': 'copy-template',
            'type': str,
            'default': '',
            'help': 'Copy a built-in template into templates/ or your theme',
        },
        {
            'name': 'new',
            'short': 'n',
            'long': 'new',
            'type': str,
            'default': '',
            'help': 'Create a new theme',
        },
        {
            'name': 'new_engine',
            'long': 'engine',
            'type': str,
            'default': 'mako',
            'help': 'Engine to use for new theme (mako or jinja -- default: mako)',
        },
        {
            'name': 'new_parent',
            'long': 'parent',
            'type': str,
            'default': 'base',
            'help': 'Parent to use for new theme (default: base)',
        },
    ]

    def _execute(self, options, args):
        """Install theme into current site."""
        url = options['url']

        # See the "mode" we need to operate in
        install = options.get('install')
        uninstall = options.get('uninstall')
        list_available = options.get('list')
        list_installed = options.get('list_installed')
        get_path = options.get('getpath')
        copy_template = options.get('copy-template')
        new = options.get('new')
        new_engine = options.get('new_engine')
        new_parent = options.get('new_parent')
        command_count = [bool(x) for x in (
            install,
            uninstall,
            list_available,
            list_installed,
            get_path,
            copy_template,
            new)].count(True)
        if command_count > 1 or command_count == 0:
            print(self.help())
            return 2

        if list_available:
            return self.list_available(url)
        elif list_installed:
            return self.list_installed()
        elif install:
            return self.do_install_deps(url, install)
        elif uninstall:
            return self.do_uninstall(uninstall)
        elif get_path:
            return self.get_path(get_path)
        elif copy_template:
            return self.copy_template(copy_template)
        elif new:
            return self.new_theme(new, new_engine, new_parent)

    def do_install_deps(self, url, name):
        """Install themes and their dependencies."""
        data = self.get_json(url)
        # `name` may be modified by the while loop.
        origname = name
        installstatus = self.do_install(name, data)
        # See if the theme's parent is available. If not, install it
        while True:
            parent_name = utils.get_parent_theme_name(utils.get_theme_path_real(name, self.site.themes_dirs))
            if parent_name is None:
                break
            try:
                utils.get_theme_path_real(parent_name, self.site.themes_dirs)
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
                theme_path = utils.get_theme_path_real(name, self.site.themes_dirs)
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
            path = utils.get_theme_path_real(name, self.site.themes_dirs)
        except Exception:
            LOGGER.error('Unknown theme: {0}'.format(name))
            return 1
        # Don't uninstall builtin themes (Issue #2510)
        blocked = os.path.dirname(utils.__file__)
        if path.startswith(blocked):
            LOGGER.error("Can't delete builtin theme: {0}".format(name))
            return 1
        LOGGER.warning('About to uninstall theme: {0}'.format(name))
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
            path = utils.get_theme_path_real(name, self.site.themes_dirs)
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

    def list_installed(self):
        """List all installed themes."""
        print("Installed Themes:")
        print("-----------------")
        themes = []
        themes_dirs = self.site.themes_dirs + [resource_filename('nikola', os.path.join('data', 'themes'))]
        for tdir in themes_dirs:
            themes += [(i, os.path.join(tdir, i)) for i in os.listdir(tdir)]
        for tname, tpath in sorted(set(themes)):
            if os.path.isdir(tpath):
                print("{0} at {1}".format(tname, tpath))

    def copy_template(self, template):
        """Copy the named template file from the parent to a local theme or to templates/."""
        # Find template
        t = self.site.template_system.get_template_path(template)
        if t is None:
            LOGGER.error("Cannot find template {0} in the lookup.".format(template))
            return 2

        # Figure out where to put it.
        # Check if a local theme exists.
        theme_path = utils.get_theme_path(self.site.THEMES[0])
        if theme_path.startswith('themes' + os.sep):
            # Theme in local themes/ directory
            base = os.path.join(theme_path, 'templates')
        else:
            # Put it in templates/
            base = 'templates'

        if not os.path.exists(base):
            os.mkdir(base)
            LOGGER.info("Created directory {0}".format(base))

        try:
            out = shutil.copy(t, base)
            LOGGER.info("Copied template from {0} to {1}".format(t, out))
        except shutil.SameFileError:
            LOGGER.error("This file already exists in your templates directory ({0}).".format(base))
            return 3

    def new_theme(self, name, engine, parent):
        """Create a new theme."""
        base = 'themes'
        themedir = os.path.join(base, name)
        LOGGER.info("Creating theme {0} with parent {1} and engine {2} in {3}".format(name, parent, engine, themedir))
        if not os.path.exists(base):
            os.mkdir(base)
            LOGGER.info("Created directory {0}".format(base))

        # Check if engine and parent match
        engine_file = utils.get_asset_path('engine', utils.get_theme_chain(parent, self.site.themes_dirs))
        with io.open(engine_file, 'r', encoding='utf-8') as fh:
            parent_engine = fh.read().strip()

        if parent_engine != engine:
            LOGGER.error("Cannot use engine {0} because parent theme '{1}' uses {2}".format(engine, parent, parent_engine))
            return 2

        # Create theme
        if not os.path.exists(themedir):
            os.mkdir(themedir)
            LOGGER.info("Created directory {0}".format(themedir))
        else:
            LOGGER.error("Theme already exists")
            return 2

        with io.open(os.path.join(themedir, 'parent'), 'w', encoding='utf-8') as fh:
            fh.write(parent + '\n')
            LOGGER.info("Created file {0}".format(os.path.join(themedir, 'parent')))
        with io.open(os.path.join(themedir, 'engine'), 'w', encoding='utf-8') as fh:
            fh.write(engine + '\n')
            LOGGER.info("Created file {0}".format(os.path.join(themedir, 'engine')))

        LOGGER.info("Theme {0} created successfully.".format(themedir))
        LOGGER.notice('Remember to set THEME="{0}" in conf.py to use this theme.'.format(name))

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
