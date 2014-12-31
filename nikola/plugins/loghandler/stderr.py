# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Daniel Devine and others.

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

from nikola.plugin_categories import SignalHandler
from blinker import signal
import os

from nikola import DEBUG
from nikola.utils import ColorfulStderrHandler


class StderrHandler(SignalHandler):
    """Logs messages to stderr."""
    name = 'stderr'

    def attach_handler(self, sender):
        """Attach the handler to the logger."""
        conf = self.site.config.get('LOGGING_HANDLERS').get('stderr')
        if conf or os.getenv('NIKOLA_DEBUG'):
            self.site.loghandlers.append(ColorfulStderrHandler(
                # We do not allow the level to be something else than 'DEBUG'
                # or 'INFO'  Any other level can have bad effects on the user
                # experience and is discouraged.
                # (oh, and it was incorrectly set to WARNING before)
                level='DEBUG' if DEBUG or (conf.get('loglevel', 'INFO').upper() == 'DEBUG') else 'INFO',
                format_string=u'[{record.time:%Y-%m-%dT%H:%M:%SZ}] {record.level_name}: {record.channel}: {record.message}'
            ))

    def set_site(self, site):
        self.site = site

        ready = signal('sighandlers_loaded')
        ready.connect(self.attach_handler)
