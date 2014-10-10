# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils

LOGGER = utils.get_logger('bootswatch_theme', utils.STDERR_HANDLER)


class CommandBootswatchTheme(Command):
    """Given a swatch name from bootswatch.com and a parent theme, creates a custom theme."""

    name = "bootswatch_theme"
    doc_usage = "[options]"
    doc_purpose = "given a swatch name from bootswatch.com and a parent theme, creates a custom"\
        " theme"
    cmd_options = [
        {
            'name': 'name',
            'short': 'n',
            'long': 'name',
            'default': 'custom',
            'type': str,
            'help': 'New theme name (default: custom)',
        },
        {
            'name': 'swatch',
            'short': 's',
            'default': 'slate',
            'type': str,
            'help': 'Name of the swatch from bootswatch.com.'
        },
        {
            'name': 'parent',
            'short': 'p',
            'long': 'parent',
            'default': 'bootstrap3',
            'help': 'Parent theme name (default: bootstrap3)',
        },
    ]

    def _execute(self, options, args):
        """Given a swatch name and a parent theme, creates a custom theme."""
        if requests is None:
            utils.req_missing(['requests'], 'install Bootswatch themes')

        name = options['name']
        swatch = options['swatch']
        parent = options['parent']
        version = ''

        # See if we need bootswatch for bootstrap v2 or v3
        themes = utils.get_theme_chain(parent)
        if 'bootstrap3' not in themes and 'bootstrap3-jinja' not in themes:
            version = '2'
        elif 'bootstrap' not in themes and 'bootstrap-jinja' not in themes:
            LOGGER.warn('"bootswatch_theme" only makes sense for themes that use bootstrap')
        elif 'bootstrap3-gradients' in themes or 'bootstrap3-gradients-jinja' in themes:
            LOGGER.warn('"bootswatch_theme" doesn\'t work well with the bootstrap3-gradients family')

        LOGGER.info("Creating '{0}' theme from '{1}' and '{2}'".format(name, swatch, parent))
        utils.makedirs(os.path.join('themes', name, 'assets', 'css'))
        for fname in ('bootstrap.min.css', 'bootstrap.css'):
            url = 'http://bootswatch.com'
            if version:
                url += '/' + version
            url = '/'.join((url, swatch, fname))
            LOGGER.info("Downloading: " + url)
            data = requests.get(url).text
            with open(os.path.join('themes', name, 'assets', 'css', fname),
                      'wb+') as output:
                output.write(data.encode('utf-8'))

        with open(os.path.join('themes', name, 'parent'), 'wb+') as output:
            output.write(parent.encode('utf-8'))
        LOGGER.notice('Theme created.  Change the THEME setting to "{0}" to use it.'.format(name))
