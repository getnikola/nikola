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

"""Given a swatch name from bootswatch.com and a parent theme, creates a custom theme."""

from __future__ import print_function
import os
import requests

from nikola.plugin_categories import Command
from nikola import utils

LOGGER = utils.get_logger('bootswatch_theme', utils.STDERR_HANDLER)


def _check_for_theme(theme, themes):
    for t in themes:
        if t.endswith(os.sep + theme):
            return True
    return False


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
            'default': '',
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
        name = options['name']
        swatch = options['swatch']
        if not swatch:
            LOGGER.error('The -s option is mandatory')
            return 1
        parent = options['parent']
        version = ''

        # See if we need bootswatch for bootstrap v2 or v3
        themes = utils.get_theme_chain(parent, self.site.themes_dirs)
        if not _check_for_theme('bootstrap3', themes) and not _check_for_theme('bootstrap3-jinja', themes):
            version = '2'
        elif not _check_for_theme('bootstrap', themes) and not _check_for_theme('bootstrap-jinja', themes):
            LOGGER.warn('"bootswatch_theme" only makes sense for themes that use bootstrap')
        elif _check_for_theme('bootstrap3-gradients', themes) or _check_for_theme('bootstrap3-gradients-jinja', themes):
            LOGGER.warn('"bootswatch_theme" doesn\'t work well with the bootstrap3-gradients family')

        LOGGER.info("Creating '{0}' theme from '{1}' and '{2}'".format(name, swatch, parent))
        utils.makedirs(os.path.join('themes', name, 'assets', 'css'))
        for fname in ('bootstrap.min.css', 'bootstrap.css'):
            url = 'https://bootswatch.com'
            if version:
                url += '/' + version
            url = '/'.join((url, swatch, fname))
            LOGGER.info("Downloading: " + url)
            r = requests.get(url)
            if r.status_code > 299:
                LOGGER.error('Error {} getting {}', r.status_code, url)
                exit(1)
            data = r.text
            with open(os.path.join('themes', name, 'assets', 'css', fname),
                      'wb+') as output:
                output.write(data.encode('utf-8'))

        with open(os.path.join('themes', name, 'parent'), 'wb+') as output:
            output.write(parent.encode('utf-8'))
        LOGGER.notice('Theme created.  Change the THEME setting to "{0}" to use it.'.format(name))
