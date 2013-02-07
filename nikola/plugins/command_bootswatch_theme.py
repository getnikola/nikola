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
from optparse import OptionParser
import os

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command


class CommandBootswatchTheme(Command):
    """Given a swatch name and a parent theme, creates a custom theme."""

    name = "bootswatch_theme"

    def run(self, *args):
        """Given a swatch name and a parent theme, creates a custom theme."""
        if requests is None:
            print('To use the install_theme command, you need to install the '
                  '"requests" package.')
            return
        parser = OptionParser(usage="nikola %s [options]" % self.name)
        parser.add_option("-n", "--name", dest="name",
                          help="New theme name (default: custom)",
                          default='custom')
        parser.add_option("-s", "--swatch", dest="swatch",
                          help="Name of the swatch from bootswatch.com "
                          "(default: slate)", default='slate')
        parser.add_option("-p", "--parent", dest="parent",
                          help="Parent theme name (default: site)",
                          default='site')
        (options, args) = parser.parse_args(list(args))

        name = options.name
        swatch = options.swatch
        parent = options.parent

        print("Creating '%s' theme from '%s' and '%s'" % (
            name, swatch, parent))
        try:
            os.makedirs(os.path.join('themes', name, 'assets', 'css'))
        except:
            pass
        for fname in ('bootstrap.min.css', 'bootstrap.css'):
            url = 'http://bootswatch.com/%s/%s' % (swatch, fname)
            print("Downloading: ", url)
            data = requests.get(url).text
            with open(os.path.join('themes', name, 'assets', 'css', fname),
                      'wb+') as output:
                output.write(data)

        with open(os.path.join('themes', name, 'parent'), 'wb+') as output:
            output.write(parent)
        print('Theme created. Change the THEME setting to "%s" to use it.' %
              name)
