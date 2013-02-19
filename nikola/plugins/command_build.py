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

from __future__ import unicode_literals
import os
import tempfile

from nikola.plugin_categories import Command


class CommandBuild(Command):
    """Build the site."""

    name = "build"

    def run(self, *args):
        """Build the site using doit."""

        # FIXME: this is crap, do it right
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as self.dodo:
            self.dodo.write(b'''
import sys
sys.path.insert(0, '.')
from doit.reporter import ExecutedOnlyReporter
DOIT_CONFIG = {
        'reporter': ExecutedOnlyReporter,
        'default_tasks': ['render_site'],
}
from nikola import Nikola
import conf
SITE = Nikola(**conf.__dict__)


def task_render_site():
    return SITE.gen_tasks()
            ''')
            self.dodo.flush()
            first = args[0] if args else None
            if first in ('auto', 'clean', 'forget', 'ignore', 'list', 'run'):
                cmd = first
                args = args[1:]
            else:
                cmd = 'run'
            os.system('doit %s -f %s -d . %s' % (cmd, self.dodo.name,
                                                 ''.join(args)))
            os.unlink(self.dodo.name)
