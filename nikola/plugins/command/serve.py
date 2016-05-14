# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Start test server."""

from __future__ import print_function
import os
import re
import socket
import webbrowser
try:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer  # NOQA
    from http.server import SimpleHTTPRequestHandler  # NOQA

try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO  # NOQA


from nikola.plugin_categories import Command
from nikola.utils import dns_sd, get_logger, STDERR_HANDLER


class IPv6Server(HTTPServer):
    """An IPv6 HTTPServer."""

    address_family = socket.AF_INET6


class CommandServe(Command):
    """Start test server."""

    name = "serve"
    doc_usage = "[options]"
    doc_purpose = "start the test webserver"
    logger = None
    dns_sd = None

    cmd_options = (
        {
            'name': 'port',
            'short': 'p',
            'long': 'port',
            'default': 8000,
            'type': int,
            'help': 'Port number (default: 8000)',
        },
        {
            'name': 'address',
            'short': 'a',
            'long': 'address',
            'type': str,
            'default': '',
            'help': 'Address to bind (default: 0.0.0.0 -- all local IPv4 interfaces)',
        },
        {
            'name': 'detach',
            'short': 'd',
            'long': 'detach',
            'type': bool,
            'default': False,
            'help': 'Detach from TTY (work in the background)',
        },
        {
            'name': 'browser',
            'short': 'b',
            'long': 'browser',
            'type': bool,
            'default': False,
            'help': 'Open the test server in a web browser',
        },
        {
            'name': 'ipv6',
            'short': '6',
            'long': 'ipv6',
            'type': bool,
            'default': False,
            'help': 'Use IPv6',
        },
    )

    def _execute(self, options, args):
        """Start test server."""
        self.logger = get_logger('serve', STDERR_HANDLER)
        out_dir = self.site.config['OUTPUT_FOLDER']
        if not os.path.isdir(out_dir):
            self.logger.error("Missing '{0}' folder?".format(out_dir))
        else:
            os.chdir(out_dir)
            if '[' in options['address']:
                options['address'] = options['address'].strip('[').strip(']')
                ipv6 = True
                OurHTTP = IPv6Server
            elif options['ipv6']:
                ipv6 = True
                OurHTTP = IPv6Server
            else:
                ipv6 = False
                OurHTTP = HTTPServer

            httpd = OurHTTP((options['address'], options['port']),
                            OurHTTPRequestHandler)
            sa = httpd.socket.getsockname()
            self.logger.info("Serving HTTP on {0} port {1}...".format(*sa))
            if options['browser']:
                if ipv6:
                    server_url = "http://[{0}]:{1}/".format(*sa)
                else:
                    server_url = "http://{0}:{1}/".format(*sa)
                self.logger.info("Opening {0} in the default web browser...".format(server_url))
                webbrowser.open(server_url)
            if options['detach']:
                OurHTTPRequestHandler.quiet = True
                try:
                    pid = os.fork()
                    if pid == 0:
                        httpd.serve_forever()
                    else:
                        self.logger.info("Detached with PID {0}. Run `kill {0}` to stop the server.".format(pid))
                except AttributeError as e:
                    if os.name == 'nt':
                        self.logger.warning("Detaching is not available on Windows, server is running in the foreground.")
                    else:
                        raise e
            else:
                try:
                    self.dns_sd = dns_sd(options['port'], (options['ipv6'] or '::' in options['address']))
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    self.logger.info("Server is shutting down.")
                    if self.dns_sd:
                        self.dns_sd.Reset()
                    return 130


class OurHTTPRequestHandler(SimpleHTTPRequestHandler):
    """A request handler, modified for Nikola."""

    extensions_map = dict(SimpleHTTPRequestHandler.extensions_map)
    extensions_map[""] = "text/plain"
    quiet = False

    def log_message(self, *args):
        """Log messages.  Or not, depending on a setting."""
        if self.quiet:
            return
        else:
            # Old-style class in Python 2.7, cannot use super()
            return SimpleHTTPRequestHandler.log_message(self, *args)

    # NOTICE: this is a patched version of send_head() to disable all sorts of
    # caching.  `nikola serve` is a development server, hence caching should
    # not happen to have access to the newest resources.
    #
    # The original code was copy-pasted from Python 2.7.  Python 3.3 contains
    # the same code, missing the binary mode comment.
    #
    # Note that it might break in future versions of Python, in which case we
    # would need to do even more magic.
    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                # begin no-cache patch
                # For redirects.  With redirects, caching is even worse and can
                # break more.  Especially with 301 Moved Permanently redirects,
                # like this one.
                self.send_header("Cache-Control", "no-cache, no-store, "
                                 "must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                # end no-cache patch
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None

        filtered_bytes = None
        if ctype == 'text/html':
            # Comment out any <base> to allow local resolution of relative URLs.
            data = f.read().decode('utf8')
            f.close()
            data = re.sub(r'<base\s([^>]*)>', '<!--base \g<1>-->', data, re.IGNORECASE)
            data = data.encode('utf8')
            f = StringIO()
            f.write(data)
            filtered_bytes = len(data)
            f.seek(0)

        self.send_response(200)
        if ctype.startswith('text/') or ctype.endswith('+xml'):
            self.send_header("Content-Type", "{0}; charset=UTF-8".format(ctype))
        else:
            self.send_header("Content-Type", ctype)
        if os.path.splitext(path)[1] == '.svgz':
            # Special handling for svgz to make it work nice with browsers.
            self.send_header("Content-Encoding", 'gzip')

        if filtered_bytes is None:
            fs = os.fstat(f.fileno())
            self.send_header('Content-Length', str(fs[6]))
        else:
            self.send_header('Content-Length', filtered_bytes)

        # begin no-cache patch
        # For standard requests.
        self.send_header("Cache-Control", "no-cache, no-store, "
                         "must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        # end no-cache patch
        self.end_headers()
        return f
