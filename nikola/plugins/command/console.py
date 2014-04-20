# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Chris Warrick, Roberto Alsina and others.

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

from doit.cmdparse import CmdParse

from nikola import __version__
from nikola.plugin_categories import Command
from nikola.utils import get_logger, STDERR_HANDLER, req_missing

LOGGER = get_logger('console', STDERR_HANDLER)


class CommandConsole(Command):
    """Start debugging console."""
    name = "console"
    shells = ['ipython', 'bpython', 'plain']
    doc_purpose = "start an interactive Python console with access to your site"
    doc_description = """\
The site engine is accessible as `site`, the config file as `conf`, and commands are available as `commands`.
If there is no console to use specified (as -b, -i, -p) it tries IPython, then falls back to bpython, and finally falls back to the plain Python console."""
    header = "Nikola v" + __version__ + " -- {0} Console (conf = configuration file, site = site engine, commands = nikola commands)"
    cmd_options = [
        {
            'name': 'bpython',
            'short': 'b',
            'long': 'bpython',
            'type': bool,
            'default': False,
            'help': 'Use bpython',
        },
        {
            'name': 'ipython',
            'short': 'i',
            'long': 'plain',
            'type': bool,
            'default': False,
            'help': 'Use IPython',
        },
        {
            'name': 'plain',
            'short': 'p',
            'long': 'plain',
            'type': bool,
            'default': False,
            'help': 'Use the plain Python interpreter',
        },
    ]

    def ipython(self, willful=True):
        """IPython shell."""
        try:
            import IPython
        except ImportError as e:
            if willful:
                req_missing(['IPython'], 'use the IPython console')
            raise e  # That’s how _execute knows whether to try something else.
        else:
            site = self.context['site']  # NOQA
            conf = self.context['conf']  # NOQA
            commands = self.context['commands']  # NOQA
            IPython.embed(header=self.header.format('IPython'))

    def bpython(self, willful=True):
        """bpython shell."""
        try:
            import bpython
        except ImportError as e:
            if willful:
                req_missing(['bpython'], 'use the bpython console')
            raise e  # That’s how _execute knows whether to try something else.
        else:
            bpython.embed(banner=self.header.format('bpython'), locals_=self.context)

    def plain(self, willful=True):
        """Plain Python shell."""
        import code
        try:
            import readline
        except ImportError:
            pass
        else:
            import rlcompleter
            readline.set_completer(rlcompleter.Completer(self.context).complete)
            readline.parse_and_bind("tab:complete")

        pythonrc = os.environ.get("PYTHONSTARTUP")
        if pythonrc and os.path.isfile(pythonrc):
            try:
                execfile(pythonrc)  # NOQA
            except NameError:
                pass

        code.interact(local=self.context, banner=self.header.format('Python'))

    def _execute(self, options, args):
        """Start the console."""
        self.site.scan_posts()
        # Create nice object with all commands:
        commands = Commands(self.site.doit)

        self.context = {
            'conf': self.site.config,
            'site': self.site,
            'commands': commands,
        }
        if options['bpython']:
            self.bpython(True)
        elif options['ipython']:
            self.ipython(True)
        elif options['plain']:
            self.plain(True)
        else:
            for shell in self.shells:
                try:
                    return getattr(self, shell)(False)
                except ImportError:
                    pass
            raise ImportError


class CommandWrapper(object):
    """Converts commands into functions."""

    def __init__(self, cmd, commands_object):
        self.cmd = cmd
        self.commands_object = commands_object

    def __call__(self, *args, **kwargs):
        if args or (not args and not kwargs):
            self.commands_object._run([self.cmd] + list(args))
        else:
            # Here's where the keyword magic would have to go
            self.commands_object._run_with_kw(self.cmd, *args, **kwargs)


class Commands(object):

    """Nikola Commands.
CommandWrapper
    Sample usage:
    >>> commands.check('-l')                     # doctest: +SKIP

    Or, if you know the internal argument names:
    >>> commands.check(list=True)                # doctest: +SKIP
    """

    def __init__(self, main):
        """Takes a main instance, works as wrapper for commands."""
        self._cmdnames = []
        for k, v in main.get_commands().items():
            self._cmdnames.append(k)
            if k in ['run', 'init']:
                continue
            nc = type(
                bytes(k),
                (CommandWrapper,),
                {
                    '__doc__': options2docstring(k, main.sub_cmds[k].options)
                })
            setattr(self, k, nc(k, self))
        self.main = main

    def _run(self, cmd_args):
        self.main.run(cmd_args)

    def _run_with_kw(self, cmd, *a, **kw):
        cmd = self.main.sub_cmds[cmd]
        options, _ = CmdParse(cmd.options).parse([])
        options.update(kw)
        if isinstance(cmd, Command):
            cmd.execute(options=options, args=a)
        else:  # Doit command
            cmd.execute(options, a)

    def __repr__(self):
        """Return useful and verbose help."""

        return """\
<Nikola Commands>

    Sample usage:
    >>> commands.check('-l')

    Or, if you know the internal argument names:
    >>> commands.check(list=True)

Available commands: {0}.""".format(', '.join(self._cmdnames))


def options2docstring(name, options):
    result = ['Function wrapper for command %s' % name, 'arguments:']
    for opt in options:
        result.append('{0} type {1} default {2}'.format(opt.name, opt.type.__name__, opt.default))
    return '\n'.join(result)
