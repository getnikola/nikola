# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Install a theme."""

from __future__ import print_function

from nikola import utils
from nikola.plugin_categories import Command
LOGGER = utils.get_logger('install_theme', utils.STDERR_HANDLER)


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
                    "https://themes.getnikola.com/v7/themes.json)",
            'default': 'https://themes.getnikola.com/v7/themes.json'
        },
        {
            'name': 'getpath',
            'short': 'g',
            'long': 'get-path',
            'type': bool,
            'default': False,
            'help': "Print the path for installed theme",
        },
    ]

    def _execute(self, options, args):
        """Install theme into current site."""
        p = self.site.plugin_manager.getPluginByName('theme', 'Command').plugin_object
        listing = options['list']
        url = options['url']
        if args:
            name = args[0]
        else:
            name = None

        if options['getpath'] and name:
            return p.get_path(name)

        if name is None and not listing:
            LOGGER.error("This command needs either a theme name or the -l option.")
            return False

        if listing:
            p.list_available(url)
        else:
            p.do_install_deps(url, name)
