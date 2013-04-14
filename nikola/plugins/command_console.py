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

from __future__ import print_function, unicode_literals

import os

from nikola.plugin_categories import Command


class Console(Command):
    """Start debugging console."""
    name = "console"
    shells = ['ipython', 'bpython', 'plain']
    doc_purpose = "Start an interactive python console with access to your site and configuration."

    def ipython(self):
        """IPython shell."""
        from nikola import Nikola
        try:
            import conf
        except ImportError:
            print("No configuration found, cannot run the console.")
        else:
            import IPython
            SITE = Nikola(**conf.__dict__)
            SITE.scan_posts()
            IPython.embed(header='Nikola Console (conf = configuration, SITE '
                          '= site engine)')

    def bpython(self):
        """bpython shell."""
        from nikola import Nikola
        try:
            import conf
        except ImportError:
            print("No configuration found, cannot run the console.")
        else:
            import bpython
            SITE = Nikola(**conf.__dict__)
            SITE.scan_posts()
            gl = {'conf': conf, 'SITE': SITE, 'Nikola': Nikola}
            bpython.embed(banner='Nikola Console (conf = configuration, SITE '
                          '= site engine)', locals_=gl)

    def plain(self):
        """Plain Python shell."""
        from nikola import Nikola
        try:
            import conf
            SITE = Nikola(**conf.__dict__)
            SITE.scan_posts()
            gl = {'conf': conf, 'SITE': SITE, 'Nikola': Nikola}
        except ImportError:
            print("No configuration found, cannot run the console.")
        else:
            import code
            try:
                import readline
            except ImportError:
                pass
            else:
                import rlcompleter
                readline.set_completer(rlcompleter.Completer(gl).complete)
                readline.parse_and_bind("tab:complete")

            pythonrc = os.environ.get("PYTHONSTARTUP")
            if pythonrc and os.path.isfile(pythonrc):
                try:
                    execfile(pythonrc)  # NOQA
                except NameError:
                    pass

            code.interact(local=gl, banner='Nikola Console (conf = '
                          'configuration, SITE = site engine)')

    def _execute(self, options, args):
        """Start the console."""
        for shell in self.shells:
            try:
                return getattr(self, shell)()
            except ImportError:
                pass
        raise ImportError
