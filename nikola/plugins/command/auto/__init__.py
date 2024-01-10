# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Chris Warrick, Roberto Alsina and others.

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

import asyncio
import datetime
import mimetypes
import os
import re
import stat
import subprocess
import sys
import typing
import urllib.parse
import webbrowser

import blinker
import pkg_resources

from nikola.plugin_categories import Command
from nikola.utils import dns_sd, req_missing, get_theme_path, makedirs

try:
    import aiohttp
    from aiohttp import web
    from aiohttp.web_urldispatcher import StaticResource
    from aiohttp.web_exceptions import HTTPNotFound, HTTPForbidden, HTTPMovedPermanently
    from aiohttp.web_response import Response
    from aiohttp.web_fileresponse import FileResponse
except ImportError:
    aiohttp = web = None
    StaticResource = HTTPNotFound = HTTPForbidden = Response = FileResponse = object

try:
    from watchdog.observers import Observer
except ImportError:
    Observer = None

LRJS_PATH = os.path.join(os.path.dirname(__file__), 'livereload.js')
REBUILDING_REFRESH_DELAY = 0.35
IDLE_REFRESH_DELAY = 0.05

if sys.platform == 'win32':
    asyncio.set_event_loop(asyncio.ProactorEventLoop())


def base_path_from_siteuri(siteuri: str) -> str:
    """Extract the path part from a URI such as site['SITE_URL'].

    The path never ends with a "/". (If only "/" is intended, it is empty.)
    """
    path = urllib.parse.urlsplit(siteuri).path
    if path.endswith("/"):
        path = path[:-1]
    return path


class CommandAuto(Command):
    """Automatic rebuilds for Nikola."""

    name = "auto"
    has_server = True
    doc_purpose = "builds and serves a site; automatically detects site changes, rebuilds, and optionally refreshes a browser"
    dns_sd = None
    delta_last_rebuild = datetime.timedelta(milliseconds=100)
    web_runner = None  # type: web.AppRunner

    cmd_options = [
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
            'default': '127.0.0.1',
            'help': 'Address to bind',
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
        {
            'name': 'process',
            'short': 'n',
            'long': 'process',
            'default': 0,
            'type': int,
            'help': 'Number of subprocesses',
            'section': 'Arguments passed to `nikola build`'
        },
        {
            'name': 'parallel-type',
            'short': 'P',
            'long': 'parallel-type',
            'default': 'process',
            'type': str,
            'help': "Parallelization mode ('process' or 'thread')",
            'section': 'Arguments passed to `nikola build`'
        },
        {
            'name': 'db-file',
            'long': 'db-file',
            'default': '.doit.db',
            'type': str,
            'help': 'Database file',
            'section': 'Arguments passed to `nikola build`'
        },
        {
            'name': 'backend',
            'long': 'backend',
            'default': 'dbm',
            'type': str,
            'help': "Database backend ('dbm', 'json', 'sqlite3')",
            'section': 'Arguments passed to `nikola build`'
        }
    ]

    def _execute(self, options, args):
        """Start the watcher."""
        self.sockets = []
        self.rebuild_queue = asyncio.Queue()
        self.reload_queue = asyncio.Queue()
        self.last_rebuild = datetime.datetime.now()
        self.is_rebuilding = False

        if aiohttp is None and Observer is None:
            req_missing(['aiohttp', 'watchdog'], 'use the "auto" command')
        elif aiohttp is None:
            req_missing(['aiohttp'], 'use the "auto" command')
        elif Observer is None:
            req_missing(['watchdog'], 'use the "auto" command')

        blinker.signal('auto_command_starting').send(self.site)

        if sys.argv[0].endswith('__main__.py'):
            self.nikola_cmd = [sys.executable, '-m', 'nikola', 'build']
        else:
            self.nikola_cmd = [sys.argv[0], 'build']

        if self.site.configuration_filename != 'conf.py':
            self.nikola_cmd.append('--conf=' + self.site.configuration_filename)

        if options and options.get('process'):
            self.nikola_cmd += ['--process={}'.format(options['process']),
                                '--parallel-type={}'.format(options['parallel-type'])]

        if options:
            self.nikola_cmd += ['--db-file={}'.format(options['db-file']),
                                '--backend={}'.format(options['backend'])]

        port = options and options.get('port')
        self.snippet = '''<script>document.write('<script src="http://'
            + (location.host || 'localhost').split(':')[0]
            + ':{0}/livereload.js?snipver=1"></'
            + 'script>')</script>
        </head>'''.format(port)

        # Deduplicate entries by using a set -- otherwise, multiple rebuilds are triggered
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
        for item in self.site.config['IMAGE_FOLDERS']:
            watched.add(item)
        for item in self.site._plugin_places:
            watched.add(item)
        watched |= self.site.registered_auto_watched_folders
        # Nikola itself (useful for developers)
        watched.add(pkg_resources.resource_filename('nikola', ''))

        out_folder = self.site.config['OUTPUT_FOLDER']
        if not os.path.exists(out_folder):
            makedirs(out_folder)

        if options and options.get('browser'):
            browser = True
        else:
            browser = False

        if options['ipv6']:
            dhost = '::'
        else:
            dhost = '0.0.0.0'

        host = options['address'].strip('[').strip(']') or dhost

        # Prepare asyncio event loop
        # Required for subprocessing to work
        loop = asyncio.get_event_loop()

        # Set debug setting
        loop.set_debug(self.site.debug)

        # Server can be disabled (Issue #1883)
        self.has_server = not options['no-server']

        base_path = base_path_from_siteuri(self.site.config['SITE_URL'])

        if self.has_server:
            loop.run_until_complete(self.set_up_server(host, port, base_path, out_folder))

        # Run an initial build so we are up-to-date. The server is running, but we are not watching yet.
        loop.run_until_complete(self.run_initial_rebuild())

        self.wd_observer = Observer()
        # Watch output folders and trigger reloads
        if self.has_server:
            self.wd_observer.schedule(NikolaEventHandler(self.reload_page, loop), out_folder, recursive=True)

        # Watch input folders and trigger rebuilds
        for p in watched:
            if os.path.exists(p):
                self.wd_observer.schedule(NikolaEventHandler(self.queue_rebuild, loop), p, recursive=True)

        # Watch config file (a bit of a hack, but we need a directory)
        _conf_fn = os.path.abspath(self.site.configuration_filename or 'conf.py')
        _conf_dn = os.path.dirname(_conf_fn)
        self.wd_observer.schedule(ConfigEventHandler(_conf_fn, self.queue_rebuild, loop), _conf_dn, recursive=False)
        self.wd_observer.start()

        win_sleeper = None
        # https://bugs.python.org/issue23057 (fixed in Python 3.8)
        if sys.platform == 'win32' and sys.version_info < (3, 8):
            win_sleeper = asyncio.ensure_future(windows_ctrlc_workaround())

        if not self.has_server:
            self.logger.info("Watching for changes...")
            # Run the event loop forever (no server mode).
            try:
                # Run rebuild queue
                loop.run_until_complete(self.run_rebuild_queue())

                loop.run_forever()
            except KeyboardInterrupt:
                pass
            finally:
                if win_sleeper:
                    win_sleeper.cancel()
                self.wd_observer.stop()
                self.wd_observer.join()
            loop.close()
            return

        if options['ipv6'] or '::' in host:
            server_url = "http://[{0}]:{1}/".format(host, port)
        else:
            server_url = "http://{0}:{1}/".format(host, port)
        self.logger.info("Serving on {0} ...".format(server_url))

        if browser:
            # Some browsers fail to load 0.0.0.0 (Issue #2755)
            if host == '0.0.0.0':
                browser_url = "http://127.0.0.1:{0}/{1}".format(port, base_path.lstrip("/"))
            else:
                # server_url always ends with a "/":
                browser_url = "{0}{1}".format(server_url, base_path.lstrip("/"))
            self.logger.info("Opening {0} in the default web browser...".format(browser_url))
            webbrowser.open(browser_url)

        # Run the event loop forever and handle shutdowns.
        try:
            # Run rebuild queue
            rebuild_queue_fut = asyncio.ensure_future(self.run_rebuild_queue())
            reload_queue_fut = asyncio.ensure_future(self.run_reload_queue())

            self.dns_sd = dns_sd(port, (options['ipv6'] or '::' in host))
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.logger.info("Server is shutting down.")
            if win_sleeper:
                win_sleeper.cancel()
            if self.dns_sd:
                self.dns_sd.Reset()
            rebuild_queue_fut.cancel()
            reload_queue_fut.cancel()
            loop.run_until_complete(self.web_runner.cleanup())
            self.wd_observer.stop()
            self.wd_observer.join()
        loop.close()

    async def set_up_server(self, host: str, port: int, base_path: str, out_folder: str) -> None:
        """Set up aiohttp server and start it."""
        webapp = web.Application()
        webapp.router.add_get('/livereload.js', self.serve_livereload_js)
        webapp.router.add_get('/robots.txt', self.serve_robots_txt)
        webapp.router.add_route('*', '/livereload', self.websocket_handler)
        resource = IndexHtmlStaticResource(True, self.snippet, base_path, out_folder)
        webapp.router.register_resource(resource)
        webapp.on_shutdown.append(self.remove_websockets)

        self.web_runner = web.AppRunner(webapp)
        await self.web_runner.setup()
        website = web.TCPSite(self.web_runner, host, port)
        await website.start()

    async def run_initial_rebuild(self) -> None:
        """Run an initial rebuild."""
        await self._rebuild_site()
        # If there are any clients, have them reload the root.
        await self._send_reload_command(self.site.config['INDEX_FILE'])

    async def queue_rebuild(self, event) -> None:
        """Rebuild the site."""
        # Move events have a dest_path, some editors like gedit use a
        # move on larger save operations for write protection
        event_path = event.dest_path if hasattr(event, 'dest_path') else event.src_path
        if sys.platform == 'win32':
            # Windows hidden files support
            is_hidden = os.stat(event_path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN
        else:
            is_hidden = False
        has_hidden_component = any(p.startswith('.') for p in event_path.split(os.sep))
        if (is_hidden or has_hidden_component or
                '__pycache__' in event_path or
                event_path.endswith(('.pyc', '.pyo', '.pyd', '_bak', '~')) or
                event.is_directory):  # Skip on folders, these are usually duplicates
            return

        self.logger.debug('Queuing rebuild from {0}'.format(event_path))
        await self.rebuild_queue.put((datetime.datetime.now(), event_path))

    async def run_rebuild_queue(self) -> None:
        """Run rebuilds from a queue (Nikola can only build in a single instance)."""
        while True:
            date, event_path = await self.rebuild_queue.get()
            if date < (self.last_rebuild + self.delta_last_rebuild):
                self.logger.debug("Skipping rebuild from {0} (within delta)".format(event_path))
                continue
            await self._rebuild_site(event_path)

    async def _rebuild_site(self, event_path: typing.Optional[str] = None) -> None:
        """Rebuild the site."""
        self.is_rebuilding = True
        self.last_rebuild = datetime.datetime.now()
        if event_path:
            self.logger.info('REBUILDING SITE (from {0})'.format(event_path))
        else:
            self.logger.info('REBUILDING SITE')

        p = await asyncio.create_subprocess_exec(*self.nikola_cmd, stderr=subprocess.PIPE)
        exit_code = await p.wait()
        out = (await p.stderr.read()).decode('utf-8')

        if exit_code != 0:
            self.logger.error("Rebuild failed\n" + out)
            await self.send_to_websockets({'command': 'alert', 'message': out})
        else:
            self.logger.info("Rebuild successful\n" + out)

        self.is_rebuilding = False

    async def run_reload_queue(self) -> None:
        """Send reloads from a queue to limit CPU usage."""
        while True:
            p = await self.reload_queue.get()
            self.logger.info('REFRESHING: {0}'.format(p))
            await self._send_reload_command(p)
            if self.is_rebuilding:
                await asyncio.sleep(REBUILDING_REFRESH_DELAY)
            else:
                await asyncio.sleep(IDLE_REFRESH_DELAY)

    async def _send_reload_command(self, path: str) -> None:
        """Send a reload command."""
        await self.send_to_websockets({'command': 'reload', 'path': path, 'liveCSS': True})

    async def reload_page(self, event) -> None:
        """Reload the page."""
        # Move events have a dest_path, some editors like gedit use a
        # move on larger save operations for write protection
        if event:
            event_path = event.dest_path if hasattr(event, 'dest_path') else event.src_path
        else:
            event_path = self.site.config['OUTPUT_FOLDER']
        p = os.path.relpath(event_path, os.path.abspath(self.site.config['OUTPUT_FOLDER'])).replace(os.sep, '/')
        await self.reload_queue.put(p)

    async def serve_livereload_js(self, request):
        """Handle requests to /livereload.js and serve the JS file."""
        return FileResponse(LRJS_PATH)

    async def serve_robots_txt(self, request):
        """Handle requests to /robots.txt."""
        return Response(body=b'User-Agent: *\nDisallow: /\n', content_type='text/plain', charset='utf-8')

    async def websocket_handler(self, request):
        """Handle requests to /livereload and initiate WebSocket communication."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.sockets.append(ws)

        while True:
            msg = await ws.receive()

            self.logger.debug("Received message: {0}".format(msg))
            if msg.type == aiohttp.WSMsgType.TEXT:
                message = msg.json()
                if message['command'] == 'hello':
                    response = {
                        'command': 'hello',
                        'protocols': [
                            'http://livereload.com/protocols/official-7',
                        ],
                        'serverName': 'Nikola Auto (livereload)',
                    }
                    await ws.send_json(response)
                elif message['command'] != 'info':
                    self.logger.warning("Unknown command in message: {0}".format(message))
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                break
            elif msg.type == aiohttp.WSMsgType.CLOSE:
                self.logger.debug("Closing WebSocket")
                await ws.close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.logger.error('WebSocket connection closed with exception {0}'.format(ws.exception()))
                break
            else:
                self.logger.warning("Received unknown message: {0}".format(msg))

        self.sockets.remove(ws)
        self.logger.debug("WebSocket connection closed: {0}".format(ws))

        return ws

    async def remove_websockets(self, app) -> None:
        """Remove all websockets."""
        for ws in self.sockets:
            await ws.close()
        self.sockets.clear()

    async def send_to_websockets(self, message: dict) -> None:
        """Send a message to all open WebSockets."""
        to_delete = []
        for ws in self.sockets:
            if ws.closed:
                to_delete.append(ws)
                continue

            try:
                await ws.send_json(message)
                if ws._close_code:
                    await ws.close()
                    to_delete.append(ws)
            except RuntimeError as e:
                if 'closed' in e.args[0]:
                    self.logger.warning("WebSocket {0} closed uncleanly".format(ws))
                    to_delete.append(ws)
                else:
                    raise

        for ws in to_delete:
            self.sockets.remove(ws)


async def windows_ctrlc_workaround() -> None:
    """Work around bpo-23057."""
    # https://bugs.python.org/issue23057
    while True:
        await asyncio.sleep(1)


class IndexHtmlStaticResource(StaticResource):
    """A StaticResource implementation that serves /index.html in directory roots."""

    modify_html = True
    snippet = "</head>"

    def __init__(self, modify_html=True, snippet="</head>", *args, **kwargs):
        """Initialize a resource."""
        self.modify_html = modify_html
        self.snippet = snippet
        super().__init__(*args, **kwargs)

    async def _handle(self, request: 'web.Request') -> 'web.Response':
        """Handle incoming requests (pass to handle_file)."""
        filename = request.match_info['filename']
        return await self.handle_file(request, filename)

    async def handle_file(self, request: 'web.Request', filename: str, from_index=None) -> 'web.Response':
        """Handle file requests."""
        try:
            filepath = self._directory.joinpath(filename).resolve()
            if not self._follow_symlinks:
                filepath.relative_to(self._directory)
        except (ValueError, FileNotFoundError) as error:
            # relatively safe
            raise HTTPNotFound() from error
        except Exception as error:
            # perm error or other kind!
            request.app.logger.exception(error)
            raise HTTPNotFound() from error

        # on opening a dir, load it's contents if allowed
        if filepath.is_dir():
            if filename.endswith('/') or not filename:
                ret = await self.handle_file(request, filename + 'index.html', from_index=filename)
            else:
                # Redirect and add trailing slash so relative links work (Issue #3140)
                new_url = request.rel_url.path + '/'
                if request.rel_url.query_string:
                    new_url += '?' + request.rel_url.query_string
                raise HTTPMovedPermanently(new_url)
        elif filepath.is_file():
            ct, encoding = mimetypes.guess_type(str(filepath))
            encoding = encoding or 'utf-8'
            if ct == 'text/html' and self.modify_html:
                if sys.version_info[0] == 3 and sys.version_info[1] <= 5:
                    # Python 3.4 and 3.5 do not accept pathlib.Path objects in calls to open()
                    filepath = str(filepath)
                with open(filepath, 'r', encoding=encoding) as fh:
                    text = fh.read()
                    text = self.transform_html(text)
                    ret = Response(text=text, content_type=ct, charset=encoding)
            else:
                ret = FileResponse(filepath, chunk_size=self._chunk_size)
        elif from_index:
            filepath = self._directory.joinpath(from_index).resolve()
            try:
                return Response(text=self._directory_as_html(filepath),
                                content_type="text/html")
            except PermissionError:
                raise HTTPForbidden
        else:
            raise HTTPNotFound

        return ret

    def transform_html(self, text: str) -> str:
        """Apply some transforms to HTML content."""
        # Inject livereload.js
        text = text.replace('</head>', self.snippet, 1)
        # Disable <base> tag
        text = re.sub(r'<base\s([^>]*)>', r'<!--base \g<1>-->', text, flags=re.IGNORECASE)
        return text


# Based on code from the 'hachiko' library by John Biesnecker — thanks!
# https://github.com/biesnecker/hachiko
class NikolaEventHandler:
    """A Nikola-specific event handler for Watchdog. Based on code from hachiko."""

    def __init__(self, function, loop):
        """Initialize the handler."""
        self.function = function
        self.loop = loop

    def dispatch(self, event):
        """Dispatch events to handler."""
        if event.event_type in {"opened", "closed"}:
            return
        self.loop.call_soon_threadsafe(asyncio.ensure_future, self.function(event))


class ConfigEventHandler(NikolaEventHandler):
    """A Nikola-specific handler for Watchdog that handles the config file (as a workaround)."""

    def __init__(self, configuration_filename, function, loop):
        """Initialize the handler."""
        super().__init__(function, loop)
        self.configuration_filename = configuration_filename

    def dispatch(self, event):
        """Handle file events if they concern the configuration file."""
        if event._src_path == self.configuration_filename:
            super().dispatch(event)
