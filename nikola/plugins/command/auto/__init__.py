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

"""Automatic rebuilds for Nikola."""

from __future__ import print_function

import json
import mimetypes
import os
import re
import subprocess
import sys
import time
try:
    from urlparse import urlparse
    from urllib2 import unquote
except ImportError:
    from urllib.parse import urlparse, unquote  # NOQA
import webbrowser
from wsgiref.simple_server import make_server
import wsgiref.util
import pkg_resources

from blinker import signal
try:
    from ws4py.websocket import WebSocket
    from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler, WebSocketWSGIHandler
    from ws4py.server.wsgiutils import WebSocketWSGIApplication
    from ws4py.messaging import TextMessage
except ImportError:
    WebSocket = object
try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, PatternMatchingEventHandler
except ImportError:
    watchdog = None
    FileSystemEventHandler = object
    PatternMatchingEventHandler = object

from nikola.plugin_categories import Command
from nikola.utils import dns_sd, req_missing, get_logger, get_theme_path, STDERR_HANDLER
LRJS_PATH = os.path.join(os.path.dirname(__file__), 'livereload.js')
error_signal = signal('error')
refresh_signal = signal('refresh')

ERROR_N = '''<html>
<head>
</head>
<boody>
ERROR {}
</body>
</html>
'''


class CommandAuto(Command):
    """Automatic rebuilds for Nikola."""

    name = "auto"
    logger = None
    has_server = True
    doc_purpose = "builds and serves a site; automatically detects site changes, rebuilds, and optionally refreshes a browser"
    dns_sd = None

    cmd_options = [
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
            'default': '127.0.0.1',
            'help': 'Address to bind (default: 127.0.0.1 -- localhost)',
        },
        {
            'name': 'browser',
            'short': 'b',
            'long': 'browser',
            'type': bool,
            'help': 'Start a web browser',
            'default': False,
        },
        {
            'name': 'ipv6',
            'short': '6',
            'long': 'ipv6',
            'default': False,
            'type': bool,
            'help': 'Use IPv6',
        },
        {
            'name': 'no-server',
            'long': 'no-server',
            'default': False,
            'type': bool,
            'help': 'Disable the server, automate rebuilds only'
        },
    ]

    def _execute(self, options, args):
        """Start the watcher."""
        self.logger = get_logger('auto', STDERR_HANDLER)
        LRSocket.logger = self.logger

        if WebSocket is object and watchdog is None:
            req_missing(['ws4py', 'watchdog'], 'use the "auto" command')
        elif WebSocket is object:
            req_missing(['ws4py'], 'use the "auto" command')
        elif watchdog is None:
            req_missing(['watchdog'], 'use the "auto" command')

        self.cmd_arguments = ['nikola', 'build']
        if self.site.configuration_filename != 'conf.py':
            self.cmd_arguments.append('--conf=' + self.site.configuration_filename)

        # Run an initial build so we are up-to-date
        subprocess.call(self.cmd_arguments)

        port = options and options.get('port')
        self.snippet = '''<script>document.write('<script src="http://'
            + (location.host || 'localhost').split(':')[0]
            + ':{0}/livereload.js?snipver=1"></'
            + 'script>')</script>
        </head>'''.format(port)

        # Do not duplicate entries -- otherwise, multiple rebuilds are triggered
        watched = set([
            'templates/'
        ] + [get_theme_path(name) for name in self.site.THEMES])
        for item in self.site.config['post_pages']:
            watched.add(os.path.dirname(item[0]))
        for item in self.site.config['FILES_FOLDERS']:
            watched.add(item)
        for item in self.site.config['GALLERY_FOLDERS']:
            watched.add(item)
        for item in self.site.config['LISTINGS_FOLDERS']:
            watched.add(item)
        for item in self.site._plugin_places:
            watched.add(item)
        # Nikola itself (useful for developers)
        watched.add(pkg_resources.resource_filename('nikola', ''))

        out_folder = self.site.config['OUTPUT_FOLDER']
        if options and options.get('browser'):
            browser = True
        else:
            browser = False

        if options['ipv6']:
            dhost = '::'
        else:
            dhost = None

        host = options['address'].strip('[').strip(']') or dhost

        # Server can be disabled (Issue #1883)
        self.has_server = not options['no-server']

        # Instantiate global observer
        observer = Observer()
        if self.has_server:
            # Watch output folders and trigger reloads
            observer.schedule(OurWatchHandler(self.do_refresh), out_folder, recursive=True)

        # Watch input folders and trigger rebuilds
        for p in watched:
            if os.path.exists(p):
                observer.schedule(OurWatchHandler(self.do_rebuild), p, recursive=True)

        # Watch config file (a bit of a hack, but we need a directory)
        _conf_fn = os.path.abspath(self.site.configuration_filename or 'conf.py')
        _conf_dn = os.path.dirname(_conf_fn)
        observer.schedule(ConfigWatchHandler(_conf_fn, self.do_rebuild), _conf_dn, recursive=False)

        try:
            self.logger.info("Watching files for changes...")
            observer.start()
        except KeyboardInterrupt:
            pass

        parent = self

        class Mixed(WebSocketWSGIApplication):
            """A class that supports WS and HTTP protocols on the same port."""

            def __call__(self, environ, start_response):
                if environ.get('HTTP_UPGRADE') is None:
                    return parent.serve_static(environ, start_response)
                return super(Mixed, self).__call__(environ, start_response)

        if self.has_server:
            ws = make_server(
                host, port, server_class=WSGIServer,
                handler_class=WebSocketWSGIRequestHandler,
                app=Mixed(handler_cls=LRSocket)
            )
            ws.initialize_websockets_manager()
            self.logger.info("Serving HTTP on {0} port {1}...".format(host, port))
            if browser:
                if options['ipv6'] or '::' in host:
                    server_url = "http://[{0}]:{1}/".format(host, port)
                else:
                    server_url = "http://{0}:{1}/".format(host, port)

                self.logger.info("Opening {0} in the default web browser...".format(server_url))
                # Yes, this is racy
                webbrowser.open('http://{0}:{1}'.format(host, port))

            try:
                self.dns_sd = dns_sd(port, (options['ipv6'] or '::' in host))
                ws.serve_forever()
            except KeyboardInterrupt:
                self.logger.info("Server is shutting down.")
                if self.dns_sd:
                    self.dns_sd.Reset()
                # This is a hack, but something is locking up in a futex
                # and exit() doesn't work.
                os.kill(os.getpid(), 15)
        else:
            # Workaround: can’t have nothing running (instant exit)
            #    but also can’t join threads (no way to exit)
            # The joys of threading.
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Shutting down.")
                # This is a hack, but something is locking up in a futex
                # and exit() doesn't work.
                os.kill(os.getpid(), 15)

    def do_rebuild(self, event):
        """Rebuild the site."""
        # Move events have a dest_path, some editors like gedit use a
        # move on larger save operations for write protection
        event_path = event.dest_path if hasattr(event, 'dest_path') else event.src_path
        fname = os.path.basename(event_path)
        if (fname.endswith('~') or
                fname.startswith('.') or
                '__pycache__' in event_path or
                event_path.endswith(('.pyc', '.pyo', '.pyd', '_bak')) or
                event.is_directory):  # Skip on folders, these are usually duplicates
            return
        self.logger.info('REBUILDING SITE (from {0})'.format(event_path))
        p = subprocess.Popen(self.cmd_arguments, stderr=subprocess.PIPE)
        error = p.stderr.read()
        errord = error.decode('utf-8')
        if p.wait() != 0:
            self.logger.error(errord)
            error_signal.send(error=errord)
        else:
            print(errord)

    def do_refresh(self, event):
        """Refresh the page."""
        # Move events have a dest_path, some editors like gedit use a
        # move on larger save operations for write protection
        event_path = event.dest_path if hasattr(event, 'dest_path') else event.src_path
        self.logger.info('REFRESHING: {0}'.format(event_path))
        p = os.path.relpath(event_path, os.path.abspath(self.site.config['OUTPUT_FOLDER']))
        refresh_signal.send(path=p)

    def serve_static(self, environ, start_response):
        """Trivial static file server."""
        uri = wsgiref.util.request_uri(environ)
        p_uri = urlparse(uri)
        f_path = os.path.join(self.site.config['OUTPUT_FOLDER'], *[unquote(x) for x in p_uri.path.split('/')])

        # ‘Pretty’ URIs and root are assumed to be HTML
        mimetype = 'text/html' if uri.endswith('/') else mimetypes.guess_type(p_uri.path)[0] or 'application/octet-stream'

        if os.path.isdir(f_path):
            if not p_uri.path.endswith('/'):  # Redirect to avoid breakage
                start_response('301 Moved Permanently', [('Location', p_uri.path + '/')])
                return []
            f_path = os.path.join(f_path, self.site.config['INDEX_FILE'])
            mimetype = 'text/html'

        if p_uri.path == '/robots.txt':
            start_response('200 OK', [('Content-type', 'text/plain; charset=UTF-8')])
            return ['User-Agent: *\nDisallow: /\n'.encode('utf-8')]
        elif os.path.isfile(f_path):
            with open(f_path, 'rb') as fd:
                if mimetype.startswith('text/') or mimetype.endswith('+xml'):
                    start_response('200 OK', [('Content-type', "{0}; charset=UTF-8".format(mimetype))])
                else:
                    start_response('200 OK', [('Content-type', mimetype)])
                return [self.file_filter(mimetype, fd.read())]
        elif p_uri.path == '/livereload.js':
            with open(LRJS_PATH, 'rb') as fd:
                start_response('200 OK', [('Content-type', mimetype)])
                return [self.file_filter(mimetype, fd.read())]
        start_response('404 ERR', [])
        return [self.file_filter('text/html', ERROR_N.format(404).format(uri).encode('utf-8'))]

    def file_filter(self, mimetype, data):
        """Apply necessary changes to document before serving."""
        if mimetype == 'text/html':
            data = data.decode('utf8')
            data = self.remove_base_tag(data)
            data = self.inject_js(data)
            data = data.encode('utf8')
        return data

    def inject_js(self, data):
        """Inject livereload.js."""
        data = re.sub('</head>', self.snippet, data, 1, re.IGNORECASE)
        return data

    def remove_base_tag(self, data):
        """Comment out any <base> to allow local resolution of relative URLs."""
        data = re.sub(r'<base\s([^>]*)>', '<!--base \g<1>-->', data, flags=re.IGNORECASE)
        return data


pending = []


class LRSocket(WebSocket):
    """Speak Livereload protocol."""

    def __init__(self, *a, **kw):
        """Initialize protocol handler."""
        refresh_signal.connect(self.notify)
        error_signal.connect(self.send_error)
        super(LRSocket, self).__init__(*a, **kw)

    def received_message(self, message):
        """Handle received message."""
        message = json.loads(message.data.decode('utf8'))
        self.logger.info('<--- {0}'.format(message))
        response = None
        if message['command'] == 'hello':  # Handshake
            response = {
                'command': 'hello',
                'protocols': [
                    'http://livereload.com/protocols/official-7',
                ],
                'serverName': 'nikola-livereload',
            }
        elif message['command'] == 'info':  # Someone connected
            self.logger.info('****** Browser connected: {0}'.format(message.get('url')))
            self.logger.info('****** sending {0} pending messages'.format(len(pending)))
            while pending:
                msg = pending.pop()
                self.logger.info('---> {0}'.format(msg.data))
                self.send(msg, msg.is_binary)
        else:
            response = {
                'command': 'alert',
                'message': 'HEY',
            }
        if response is not None:
            response = json.dumps(response)
            self.logger.info('---> {0}'.format(response))
            response = TextMessage(response)
            self.send(response, response.is_binary)

    def notify(self, sender, path):
        """Send reload requests to the client."""
        p = os.path.join('/', path)
        message = {
            'command': 'reload',
            'liveCSS': True,
            'path': p,
        }
        response = json.dumps(message)
        self.logger.info('---> {0}'.format(p))
        response = TextMessage(response)
        if self.stream is None:  # No client connected or whatever
            pending.append(response)
        else:
            self.send(response, response.is_binary)

    def send_error(self, sender, error=None):
        """Send reload requests to the client."""
        if self.stream is None:  # No client connected or whatever
            return
        message = {
            'command': 'alert',
            'message': error,
        }
        response = json.dumps(message)
        response = TextMessage(response)
        if self.stream is None:  # No client connected or whatever
            pending.append(response)
        else:
            self.send(response, response.is_binary)


class OurWatchHandler(FileSystemEventHandler):
    """A Nikola-specific handler for Watchdog."""

    def __init__(self, function):
        """Initialize the handler."""
        self.function = function
        super(OurWatchHandler, self).__init__()

    def on_any_event(self, event):
        """Call the provided function on any event."""
        self.function(event)


class ConfigWatchHandler(FileSystemEventHandler):
    """A Nikola-specific handler for Watchdog that handles the config file (as a workaround)."""

    def __init__(self, configuration_filename, function):
        """Initialize the handler."""
        self.configuration_filename = configuration_filename
        self.function = function

    def on_any_event(self, event):
        """Call the provided function on any event."""
        if event._src_path == self.configuration_filename:
            self.function(event)


try:
    # Monkeypatch to hide Broken Pipe Errors
    f = WebSocketWSGIHandler.finish_response

    if sys.version_info[0] == 3:
        EX = BrokenPipeError  # NOQA
    else:
        EX = IOError

    def finish_response(self):
        """Monkeypatched finish_response that ignores broken pipes."""
        try:
            f(self)
        except EX:  # Client closed the connection, not a real error
            pass

    WebSocketWSGIHandler.finish_response = finish_response
except NameError:
    # In case there is no WebSocketWSGIHandler because of a failed import.
    pass
