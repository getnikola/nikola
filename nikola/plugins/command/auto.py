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

from __future__ import print_function, unicode_literals

import os
import subprocess

from nikola.plugin_categories import Command
from nikola.utils import req_missing


class CommandAuto(Command):
    """Start debugging console."""
    name = "auto"
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
            'default': '',
            'help': 'Address to bind (default: 0.0.0.0 – all local IPv4 interfaces)',
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
        try:
            from livereload import Server
        except ImportError:
            req_missing(['livereload'], 'use the "auto" command')
            return

        arguments = ['build']
        if self.site.configuration_filename != 'conf.py':
            arguments = ['--conf=' + self.site.configuration_filename] + arguments

        command_line = 'nikola ' + ' '.join(arguments)

        # Run an initial build so we are up-to-date
        subprocess.call(["nikola"] + arguments)

        port = options and options.get('port')

        server = Server()
        server.watch(self.site.configuration_filename, command_line)
        server.watch('themes/', command_line)
        server.watch('templates/', command_line)
        for item in self.site.config['post_pages']:
            server.watch(os.path.dirname(item[0]), command_line)
        for item in self.site.config['FILES_FOLDERS']:
            server.watch(item, command_line)
        for item in self.site.config['GALLERY_FOLDERS']:
            server.watch(item, command_line)
        for item in self.site.config['LISTINGS_FOLDERS']:
            server.watch(item, command_line)

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

        server.serve(port=port, host=host, root=out_folder, debug=True, open_url=browser)
