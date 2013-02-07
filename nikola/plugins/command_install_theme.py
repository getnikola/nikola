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
import json
from io import BytesIO

try:
    import requests
except ImportError:
    requests = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils


class CommandInstallTheme(Command):
    """Start test server."""

    name = "install_theme"

    def run(self, *args):
        """Install theme into current site."""
        if requests is None:
            print('To use the install_theme command, you need to install the '
                  '"requests" package.')
            return
        parser = OptionParser(usage="nikola %s [options]" % self.name)
        parser.add_option("-l", "--list", dest="list", action="store_true",
                          help="Show list of available themes.")
        parser.add_option("-n", "--name", dest="name", help="Theme name",
                          default=None)
        parser.add_option("-u", "--url", dest="url", help="URL for the theme "
                          "repository" "(default: "
                          "http://nikola.ralsina.com.ar/themes/index.json)",
                          default='http://nikola.ralsina.com.ar/themes/'
                                  'index.json')
        (options, args) = parser.parse_args(list(args))

        listing = options.list
        name = options.name
        url = options.url

        if name is None and not listing:
            print("This command needs either the -n or the -l option.")
            return False
        data = requests.get(url).text
        data = json.loads(data)
        if listing:
            print("Themes:")
            print("-------")
            for theme in sorted(data.keys()):
                print(theme)
            return True
        else:
            if name in data:
                if os.path.isfile("themes"):
                    raise IOError("'themes' isn't a directory!")
                elif not os.path.isdir("themes"):
                    try:
                        os.makedirs("themes")
                    except:
                        raise OSError("mkdir 'theme' error!")
                print('Downloading: %s' % data[name])
                zip_file = BytesIO()
                zip_file.write(requests.get(data[name]).content)
                print('Extracting: %s into themes' % name)
                utils.extract_all(zip_file)
            else:
                print("Can't find theme %s" % name)
                return False
