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
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer  # NOQA
    from http.server import SimpleHTTPRequestHandler  # NOQA

from nikola.plugin_categories import Command


class CommandBuild(Command):
    """Start test server."""

    name = "serve"

    def run(self, *args):
        """Start test server."""

        parser = OptionParser(usage="nikola %s [options]" % self.name)
        parser.add_option("-p", "--port", dest="port", help="Port numer "
                          "(default: 8000)", default=8000, type="int")
        parser.add_option("-a", "--address", dest="address", help="Address to "
                          "bind (default: 127.0.0.1)", default='127.0.0.1')
        (options, args) = parser.parse_args(list(args))

        out_dir = self.site.config['OUTPUT_FOLDER']
        if not os.path.isdir(out_dir):
            print("Error: Missing '%s' folder?" % out_dir)
        else:
            os.chdir(out_dir)
            httpd = HTTPServer((options.address, options.port),
                               OurHTTPRequestHandler)
            sa = httpd.socket.getsockname()
            print("Serving HTTP on {0[0]} port {0[1]}...".format(sa))
            httpd.serve_forever()


class OurHTTPRequestHandler(SimpleHTTPRequestHandler):
    extensions_map = dict(SimpleHTTPRequestHandler.extensions_map)
    extensions_map[""] = "text/plain"
