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

import lxml
try:
    import requests
except ImportError:
    requests = None

from nikola.plugin_categories import Command
from nikola.utils import req_missing
from nikola import __version__

URL = 'https://pypi.python.org/pypi?:action=doap&name=Nikola'


class CommandVersion(Command):
    """Print the version."""

    name = "version"

    doc_usage = ""
    needs_config = False
    doc_purpose = "print the Nikola version number"
    cmd_options = [
        {
            'name': 'check',
            'long': 'check',
            'short': '',
            'default': False,
            'type': bool,
            'help': "Check for new versions.",
        }
    ]

    def _execute(self, options={}, args=None):
        """Print the version number."""
        print("Nikola v" + __version__)
        if options.get('check'):
            if requests is None:
                req_missing(['requests'], 'check for updates')
                exit(1)
            data = requests.get(URL).text
            doc = lxml.etree.fromstring(data.encode('utf8'))
            revision = doc.findall('*//{http://usefulinc.com/ns/doap#}revision')[0].text
            print("Latest version is: ", revision)
