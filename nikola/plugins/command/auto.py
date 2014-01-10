# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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
import webbrowser

from nikola.plugin_categories import Command
from nikola.utils import req_missing


class Auto(Command):
    """Start debugging console."""
    name = "auto"
    doc_purpose = "automatically detect site changes, rebuild and optionally refresh a browser"
    cmd_options = [
        {
            'name': 'browser',
            'short': 'b',
            'type': bool,
            'help': 'Start a web browser.',
            'default': False,
        },
        {
            'name': 'port',
            'short': 'p',
            'long': 'port',
            'default': 8000,
            'type': int,
            'help': 'Port nummber (default: 8000)',
        },
    ]

    def _execute(self, options, args):
        """Start the watcher."""
        try:
            from livereload import Server
        except ImportError:
            req_missing(['livereload>=2.0.0'], 'use the "auto" command')
            return

        # Run an initial build so we are uptodate
        subprocess.call(("nikola", "build"))

        port = options and options.get('port')

        server = Server()
        server.watch('conf.py')
        server.watch('themes/')
        server.watch('templates/')
        server.watch(self.site.config['GALLERY_PATH'])
        for item in self.site.config['post_pages']:
            server.watch(os.path.dirname(item[0]))
        for item in self.site.config['FILES_FOLDERS']:
            server.watch(os.path.dirname(item))

        out_folder = self.site.config['OUTPUT_FOLDER']
        if options and options.get('browser'):
            webbrowser.open('http://localhost:{0}'.format(port))

        server.serve(port, out_folder)
