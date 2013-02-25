# Copyright (c) 2012 Roberto Alsina y otros.

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


class CommandBootswatchTheme(Command):
    """Given a swatch name and a parent theme, creates a custom theme."""

    name = "bootswatch_theme"
    doc_usage = "[options]"
    doc_purpose = "Given a swatch name and a parent theme, creates a custom"\
        " theme."
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
            'default': 'site',
            'help': 'Parent theme name (default: site)',
        },
    ]

    def _execute(self, options, args):
        """Given a swatch name and a parent theme, creates a custom theme."""
        if requests is None:
            print('To use the install_theme command, you need to install the '
                  '"requests" package.')
            return

        name = options['name']
        swatch = options['swatch']
        parent = options['parent']

        print("Creating '{0}' theme from '{1}' and '{2}'".format(name, swatch,
                                                                 parent))
        try:
            os.makedirs(os.path.join('themes', name, 'assets', 'css'))
        except:
            pass
        for fname in ('bootstrap.min.css', 'bootstrap.css'):
            url = '/'.join(('http://bootswatch.com', swatch, fname))
            print("Downloading: ", url)
            data = requests.get(url).text
            with open(os.path.join('themes', name, 'assets', 'css', fname),
                      'wb+') as output:
                output.write(data)

        with open(os.path.join('themes', name, 'parent'), 'wb+') as output:
            output.write(parent)
        print('Theme created. Change the THEME setting to "{0}" to use '
              'it.'.format(name))
