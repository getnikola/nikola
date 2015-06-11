# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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

import json
import mimetypes
import os
import re
import subprocess
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # NOQA
import webbrowser
from wsgiref.simple_server import make_server
import wsgiref.util

from blinker import signal
try:
    from ws4py.websocket import WebSocket
    from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
    from ws4py.server.wsgiutils import WebSocketWSGIApplication
    from ws4py.messaging import TextMessage
except ImportError:
    WebSocket = object
try:
    import pyinotify
    MASK = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY
except ImportError:
    pyinotify = None
    MASK = None


from nikola.plugin_categories import Command
from nikola.utils import req_missing, get_logger

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
    """Start debugging console."""
    name = "auto"
    logger = None
    doc_purpose = "builds and serves a site; automatically detects site changes, rebuilds, and optionally refreshes a browser"
    cmd_options = [
        {
            'name': 'port',
            'short': 'p',
            'long': 'port',
            'default': 8000,
            'type': int,
            'help': 'Port nummber (default: 8000)',
        },
        {
            'name': 'address',
            'short': 'a',
            'long': 'address',
            'type': str,
            'default': '127.0.0.1',
            'help': 'Address to bind (default: 127.0.0.1 – localhost)',
        },
        {
            'name': 'browser',
            'short': 'b',
            'type': bool,
            'help': 'Start a web browser.',
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
    ]

    def _execute(self, options, args):
        """Start the watcher."""

        self.logger = get_logger('auto', self.site.loghandlers)
        LRSocket.logger = self.logger

        if WebSocket is object and pyinotify is None:
            req_missing(['ws4py', 'pyinotify'], 'use the "auto" command')
        elif WebSocket is object:
            req_missing(['ws4py'], 'use the "auto" command')
        elif pyinotify is None:
            req_missing(['pyinotify'], 'use the "auto" command')

        self.cmd_arguments = ['build']
        if self.site.configuration_filename != 'conf.py':
            self.cmd_arguments = ['--conf=' + self.site.configuration_filename] + self.cmd_arguments

        # Run an initial build so we are up-to-date
        subprocess.call(["nikola"] + self.cmd_arguments)

        port = options and options.get('port')
        self.snippet = '''<script>document.write('<script src="http://'
            + (location.host || 'localhost').split(':')[0]
            + ':{0}/livereload.js?snipver=1"></'
            + 'script>')</script>
        </head>'''.format(port)

        watched = [
            self.site.configuration_filename,
            'themes/',
            'templates/',
        ]
        for item in self.site.config['post_pages']:
            watched.append(os.path.dirname(item[0]))
        for item in self.site.config['FILES_FOLDERS']:
            watched.append(item)
        for item in self.site.config['GALLERY_FOLDERS']:
            watched.append(item)
        for item in self.site.config['LISTINGS_FOLDERS']:
            watched.append(item)

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

        # Start watchers that trigger reloads
        reload_wm = pyinotify.WatchManager()
        reload_notifier = pyinotify.ThreadedNotifier(reload_wm, self.do_refresh)
        reload_notifier.start()
        reload_wm.add_watch(out_folder, MASK, rec=True)  # Watch output folders

        # Start watchers that trigger rebuilds
        rebuild_wm = pyinotify.WatchManager()
        rebuild_notifier = pyinotify.ThreadedNotifier(rebuild_wm, self.do_rebuild)
        rebuild_notifier.start()
        for p in watched:
            if os.path.exists(p):
                rebuild_wm.add_watch(p, MASK, rec=True)  # Watch input folders

        parent = self

        class Mixed(WebSocketWSGIApplication):
            """A class that supports WS and HTTP protocols in the same port."""
            def __call__(self, environ, start_response):
                if environ.get('HTTP_UPGRADE') is None:
                    return parent.serve_static(environ, start_response)
                return super(Mixed, self).__call__(environ, start_response)

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
            ws.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Server is shutting down.")
            # This is a hack, but something is locking up in a futex
            # and exit() doesn't work.
            os.kill(os.getpid(), 15)

    def do_rebuild(self, event):
        p = subprocess.Popen(self.cmd_arguments, stderr=subprocess.PIPE)
        if p.wait() != 0:
            error = p.stderr.read()
            self.logger.error(error)
            error_signal.send(error=error)

    def do_refresh(self, event):
        self.logger.info('REFRESHING: {0}'.format(event.pathname))
        p = os.path.relpath(event.pathname, os.path.abspath(self.site.config['OUTPUT_FOLDER']))
        refresh_signal.send(path=p)

    def serve_static(self, environ, start_response):
        """Trivial static file server."""
        uri = wsgiref.util.request_uri(environ)
        p_uri = urlparse(uri)
        f_path = os.path.join(self.site.config['OUTPUT_FOLDER'], *p_uri.path.split('/'))
        mimetype = mimetypes.guess_type(uri)[0] or b'text/html'

        if os.path.isdir(f_path):
            f_path = os.path.join(f_path, self.site.config['INDEX_FILE'])

        if p_uri.path == '/robots.txt':
            start_response(b'200 OK', [(b'Content-type', 'txt/plain')])
            return '''User-Agent: *\nDisallow: /\n'''
        elif os.path.isfile(f_path):
            with open(f_path) as fd:
                start_response(b'200 OK', [(b'Content-type', mimetype)])
                return self.inject_js(mimetype, fd.read())
        elif p_uri.path == '/livereload.js':
            with open(LRJS_PATH) as fd:
                start_response(b'200 OK', [(b'Content-type', mimetype)])
                return self.inject_js(mimetype, fd.read())
        start_response(b'404 ERR', [])
        return self.inject_js('text/html', ERROR_N.format(404).format(uri))

    def inject_js(self, mimetype, data):
        """Inject livereload.js in HTML files."""
        if mimetype == 'text/html':
            data = re.sub('</head>', self.snippet, data, 1, re.IGNORECASE)
        return data


pending = []


class LRSocket(WebSocket):
    """Speak Livereload protocol."""

    def __init__(self, *a, **kw):
        refresh_signal.connect(self.notify)
        error_signal.connect(self.send_error)
        super(LRSocket, self).__init__(*a, **kw)

    def received_message(self, message):
        message = json.loads(message.data)
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
