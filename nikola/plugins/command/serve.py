# -*- coding: utf-8 -*-

# Copyright © 2012-2025 Roberto Alsina and others.

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
import atexit
import errno
import os
import sys
import re
import signal
import socket
import threading
import webbrowser
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from io import BytesIO as StringIO
from threading import Thread, current_thread
from typing import Callable, Optional

from nikola.plugin_categories import Command
from nikola.utils import base_path_from_siteuri, dns_sd


class IPv6Server(HTTPServer):
    """An IPv6 HTTPServer."""

    address_family = socket.AF_INET6


class CommandServe(Command):
    """Start test server."""

    name = "serve"
    doc_usage = "[options]"
    doc_purpose = "start the test webserver"
    httpd: Optional[HTTPServer] = None
    httpd_serving_thread: Optional[Thread] = None

    cmd_options = (
        {
            'name': 'port',
            'short': 'p',
            'long': 'port',
            'default': 8000,
            'type': int,
            'help': 'Port number',
        },
        {
            'name': 'address',
            'short': 'a',
            'long': 'address',
            'type': str,
            'default': '',
            'help': 'Address to bind, defaults to all local IPv4 interfaces',
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

    def shutdown(self, signum=None, _frame=None):
        """Shut down the server."""
        if os.path.exists(self.serve_pidfile):
            os.remove(self.serve_pidfile)

        # Deal with the non-detached state:
        if self.httpd is not None and self.httpd_serving_thread is not None and self.httpd_serving_thread != current_thread():
            shut_me_down = self.httpd
            self.httpd = None
            self.httpd_serving_thread = None
            self.logger.info("Web server is shutting down.")
            shut_me_down.shutdown()
        else:
            self.logger.debug("No need to shut down the web server.")

        # If this was called as a signal handler, shut down the entire application:
        if signum:
            sys.exit(0)

    def _execute(self, options, args):
        """Start test server."""
        out_dir = self.site.config['OUTPUT_FOLDER']
        if not os.path.isdir(out_dir):
            self.logger.error("Missing '{0}' folder?".format(out_dir))
        else:
            self.serve_pidfile = os.path.abspath('nikolaserve.pid')
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

            base_path = base_path_from_siteuri(self.site.config['BASE_URL'])
            if base_path == "":
                handler_factory = OurHTTPRequestHandler
            else:
                handler_factory = _create_RequestHandler_removing_basepath(base_path)

            try:
                self.httpd = OurHTTP((options['address'], options['port']), handler_factory)
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    self.logger.error(f"Port address {options['port']} already in use, please use "
                                      "the `-p <port>` option to select a different one.")
                    return 3
                else:
                    raise

            sa = self.httpd.socket.getsockname()
            if ipv6:
                server_url = "http://[{0}]:{1}/".format(*sa) + base_path
            else:
                server_url = "http://{0}:{1}/".format(*sa) + base_path
            self.logger.info("Serving on {0} ...".format(server_url))

            if options['browser']:
                # Some browsers fail to load 0.0.0.0 (Issue #2755)
                if sa[0] == '0.0.0.0':
                    server_url = "http://127.0.0.1:{1}/".format(*sa) + base_path
                self.logger.info("Opening {0} in the default web browser...".format(server_url))
                webbrowser.open(server_url)
            if options['detach']:
                OurHTTPRequestHandler.quiet = True
                try:
                    pid = os.fork()
                    if pid == 0:
                        signal.signal(signal.SIGTERM, self.shutdown)
                        self.httpd.serve_forever()
                    else:
                        with open(self.serve_pidfile, 'w') as fh:
                            fh.write('{0}\n'.format(pid))
                        self.logger.info("Detached with PID {0}. Run `kill {0}` or `kill $(cat nikolaserve.pid)` to stop the server.".format(pid))
                except AttributeError:
                    if os.name == 'nt':
                        self.logger.warning("Detaching is not available on Windows, server is running in the foreground.")
                    else:
                        raise
            else:
                try:
                    dns_socket_publication = dns_sd(options['port'], (options['ipv6'] or '::' in options['address']))
                    try:
                        self.httpd_serving_thread = threading.current_thread()
                        if threading.main_thread() == self.httpd_serving_thread:
                            # If we are running as the main thread,
                            # likely no other threads are running and nothing else will run after us.
                            # In this special case, we take some responsibility for the application whole
                            # (not really the job of any single plugin).
                            # Clean up the socket publication on exit (if we actually had a socket publication):
                            if dns_socket_publication is not None:
                                atexit.register(dns_socket_publication.Reset)
                            # Enable application shutdown via SIGTERM:
                            signal.signal(signal.SIGTERM, self.shutdown)
                        self.logger.info("Starting web server.")
                        self.httpd.serve_forever()
                        self.logger.info("Web server has shut down.")
                    finally:
                        if dns_socket_publication is not None:
                            dns_socket_publication.Reset()
                except KeyboardInterrupt:
                    self.shutdown()
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
            return super().log_message(*args)

    # NOTICE: this is a patched version of send_head() to disable all sorts of
    # caching.  `nikola serve` is a development server, hence caching should
    # not happen, instead, we should give access to the newest resources.
    #
    # The original code was copy-pasted from Python 2.7.  Python 3.3 contains
    # the same code, missing the binary mode comment.
    #
    # Note that it might break in future versions of Python, in which case we
    # would need to do even more magic.
    def send_head(self):
        """Send response code and MIME header.

        This is common code for GET and HEAD commands.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)

        f = None
        if os.path.isdir(path):
            path_parts = list(self.path.partition('?'))
            if not path_parts[0].endswith('/'):
                # redirect browser - doing basically what apache does
                path_parts[0] += '/'
                self.send_response(301)
                self.send_header("Location", ''.join(path_parts))
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
            self.send_error(404, "File not found: {}".format(path))
            return None

        filtered_bytes = None
        if ctype == 'text/html':
            # Comment out any <base> to allow local resolution of relative URLs.
            data = f.read().decode('utf8')
            f.close()
            data = re.sub(r'<base\s([^>]*)>', r'<!--base \g<1>-->', data, flags=re.IGNORECASE)
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


def _omit_basepath_component(base_path_with_slash: str, path: str) -> str:
    if path.startswith(base_path_with_slash):
        return path[len(base_path_with_slash) - 1:]
    elif path == base_path_with_slash[:-1]:
        return "/"
    else:
        # Somewhat dubious. We should not really get asked this, normally.
        return path


def _create_RequestHandler_removing_basepath(base_path: str) -> Callable:
    """Create a new subclass of OurHTTPRequestHandler that removes a trailing base path from the path.

    Returns that class (used as a factory for objects).
    Better return type should be Callable[[...], OurHTTPRequestHandler], but Python 3.8 doesn't understand that.
    """
    base_path_with_slash = base_path if base_path.endswith("/") else f"{base_path}/"

    class OmitBasepathRequestHandler(OurHTTPRequestHandler):

        def translate_path(self, path: str) -> str:
            return super().translate_path(_omit_basepath_component(base_path_with_slash, path))

    return OmitBasepathRequestHandler
