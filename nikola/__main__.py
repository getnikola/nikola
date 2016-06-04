# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""The main function of Nikola."""

from __future__ import print_function, unicode_literals
from collections import defaultdict
import os
import shutil
try:
    import readline  # NOQA
except ImportError:
    pass  # This is only so raw_input/input does nicer things if it's available
import sys
import traceback

from doit.loader import generate_tasks
from doit.cmd_base import TaskLoader
from doit.reporter import ExecutedOnlyReporter
from doit.doit_cmd import DoitMain
from doit.cmd_help import Help as DoitHelp
from doit.cmd_run import Run as DoitRun
from doit.cmd_clean import Clean as DoitClean
from doit.cmd_completion import TabCompletion
from doit.cmd_auto import Auto as DoitAuto
from logbook import NullHandler
from blinker import signal

from . import __version__
from .plugin_categories import Command
from .nikola import Nikola
from .utils import sys_decode, sys_encode, get_root_dir, req_missing, LOGGER, STRICT_HANDLER, STDERR_HANDLER, ColorfulStderrHandler

if sys.version_info[0] == 3:
    import importlib.machinery
else:
    import imp

config = {}

# DO NOT USE unless you know what you are doing!
_RETURN_DOITNIKOLA = False


def main(args=None):
    """Run Nikola."""
    colorful = False
    if sys.stderr.isatty() and os.name != 'nt' and os.getenv('NIKOLA_MONO') is None:
        colorful = True

    ColorfulStderrHandler._colorful = colorful

    if args is None:
        args = sys.argv[1:]

    oargs = args
    args = [sys_decode(arg) for arg in args]

    conf_filename = 'conf.py'
    conf_filename_bytes = b'conf.py'
    conf_filename_changed = False
    for index, arg in enumerate(args):
        if arg[:7] == '--conf=':
            del args[index]
            del oargs[index]
            conf_filename = arg[7:]
            conf_filename_bytes = sys_encode(arg[7:])
            conf_filename_changed = True
            break

    quiet = False
    strict = False
    if len(args) > 0 and args[0] == 'build' and '--strict' in args:
        LOGGER.notice('Running in strict mode')
        STRICT_HANDLER.push_application()
        strict = True
    if len(args) > 0 and args[0] == 'build' and '-q' in args or '--quiet' in args:
        NullHandler().push_application()
        quiet = True
    if not quiet and not strict:
        NullHandler().push_application()
        STDERR_HANDLER[0].push_application()

    global config

    original_cwd = os.getcwd()

    # Those commands do not require a `conf.py`.  (Issue #1132)
    # Moreover, actually having one somewhere in the tree can be bad, putting
    # the output of that command (the new site) in an unknown directory that is
    # not the current working directory.  (does not apply to `version`)
    argname = args[0] if len(args) > 0 else None
    if argname and argname not in ['init', 'version'] and not argname.startswith('import_'):
        root = get_root_dir()
        if root:
            os.chdir(root)
        # Help and imports don't require config, but can use one if it exists
        needs_config_file = (argname != 'help') and not argname.startswith('import_')
    else:
        needs_config_file = False

    sys.path.append('')
    try:
        if sys.version_info[0] == 3:
            loader = importlib.machinery.SourceFileLoader("conf", conf_filename)
            conf = loader.load_module()
        else:
            conf = imp.load_source("conf", conf_filename_bytes)
        config = conf.__dict__
    except Exception:
        if os.path.exists(conf_filename):
            msg = traceback.format_exc(0)
            LOGGER.error('"{0}" cannot be parsed.\n{1}'.format(conf_filename, msg))
            return 1
        elif needs_config_file and conf_filename_changed:
            LOGGER.error('Cannot find configuration file "{0}".'.format(conf_filename))
            return 1
        config = {}

    if conf_filename_changed:
        LOGGER.info("Using config file '{0}'".format(conf_filename))

    invariant = False

    if len(args) > 0 and args[0] == 'build' and '--invariant' in args:
        try:
            import freezegun
            freeze = freezegun.freeze_time("2038-01-01")
            freeze.start()
            invariant = True
        except ImportError:
            req_missing(['freezegun'], 'perform invariant builds')

    if config:
        if os.path.exists('plugins') and not os.path.exists('plugins/__init__.py'):
            with open('plugins/__init__.py', 'w') as fh:
                fh.write('# Plugin modules go here.')

    config['__colorful__'] = colorful
    config['__invariant__'] = invariant
    config['__quiet__'] = quiet
    config['__configuration_filename__'] = conf_filename
    config['__cwd__'] = original_cwd
    site = Nikola(**config)
    DN = DoitNikola(site, quiet)
    if _RETURN_DOITNIKOLA:
        return DN
    _ = DN.run(oargs)

    if site.invariant:
        freeze.stop()
    return _


class Help(DoitHelp):
    """Show Nikola usage."""

    @staticmethod
    def print_usage(cmds):
        """Print nikola "usage" (basic help) instructions."""
        # Remove 'run'.  Nikola uses 'build', though we support 'run' for
        # people used to it (eg. doit users).
        # WARNING: 'run' is the vanilla doit command, without support for
        #          --strict, --invariant and --quiet.
        del cmds['run']

        print("Nikola is a tool to create static websites and blogs. For full documentation and more information, please visit https://getnikola.com/\n\n")
        print("Available commands:")
        for cmd_name in sorted(cmds.keys()):
            cmd = cmds[cmd_name]
            print("  nikola {:20s} {}".format(cmd_name, cmd.doc_purpose))
        print("")
        print("  nikola help                 show help / reference")
        print("  nikola help <command>       show command usage")
        print("  nikola help <task-name>     show task usage")


class Build(DoitRun):
    """Expose "run" command as "build" for backwards compatibility."""

    def __init__(self, *args, **kw):
        """Initialize Build."""
        opts = list(self.cmd_options)
        opts.append(
            {
                'name': 'strict',
                'long': 'strict',
                'default': False,
                'type': bool,
                'help': "Fail on things that would normally be warnings.",
            }
        )
        opts.append(
            {
                'name': 'invariant',
                'long': 'invariant',
                'default': False,
                'type': bool,
                'help': "Generate invariant output (for testing only!).",
            }
        )
        opts.append(
            {
                'name': 'quiet',
                'long': 'quiet',
                'short': 'q',
                'default': False,
                'type': bool,
                'help': "Run quietly.",
            }
        )
        self.cmd_options = tuple(opts)
        super(Build, self).__init__(*args, **kw)


class Clean(DoitClean):
    """Clean site, including the cache directory."""

    def clean_tasks(self, tasks, dryrun):
        """Clean tasks."""
        if not dryrun and config:
            cache_folder = config.get('CACHE_FOLDER', 'cache')
            if os.path.exists(cache_folder):
                shutil.rmtree(cache_folder)
        return super(Clean, self).clean_tasks(tasks, dryrun)

# Nikola has its own "auto" commands that uses livereload.
# Expose original doit "auto" command as "doit_auto".
DoitAuto.name = 'doit_auto'


class NikolaTaskLoader(TaskLoader):
    """Nikola-specific task loader."""

    def __init__(self, nikola, quiet=False):
        """Initialize the loader."""
        self.nikola = nikola
        self.quiet = quiet

    def load_tasks(self, cmd, opt_values, pos_args):
        """Load Nikola tasks."""
        if self.quiet:
            DOIT_CONFIG = {
                'verbosity': 0,
                'reporter': 'zero',
            }
        else:
            DOIT_CONFIG = {
                'reporter': ExecutedOnlyReporter,
                'outfile': sys.stderr,
            }
        DOIT_CONFIG['default_tasks'] = ['render_site', 'post_render']
        DOIT_CONFIG.update(self.nikola._doit_config)
        tasks = generate_tasks(
            'render_site',
            self.nikola.gen_tasks('render_site', "Task", 'Group of tasks to render the site.'))
        latetasks = generate_tasks(
            'post_render',
            self.nikola.gen_tasks('post_render', "LateTask", 'Group of tasks to be executed after site is rendered.'))
        signal('initialized').send(self.nikola)
        return tasks + latetasks, DOIT_CONFIG


class DoitNikola(DoitMain):
    """Nikola-specific implementation of DoitMain."""

    # overwite help command
    DOIT_CMDS = list(DoitMain.DOIT_CMDS) + [Help, Build, Clean, DoitAuto]
    TASK_LOADER = NikolaTaskLoader

    def __init__(self, nikola, quiet=False):
        """Initialzie DoitNikola."""
        super(DoitNikola, self).__init__()
        self.nikola = nikola
        nikola.doit = self
        self.task_loader = self.TASK_LOADER(nikola, quiet)

    def get_cmds(self):
        """Get commands."""
        # core doit commands
        cmds = DoitMain.get_cmds(self)
        # load nikola commands
        for name, cmd in self.nikola._commands.items():
            cmds[name] = cmd
        return cmds

    def run(self, cmd_args):
        """Run Nikola."""
        args = self.process_args(cmd_args)
        args = [sys_decode(arg) for arg in args]

        if len(args) == 0:
            cmd_args = ['help']
            args = ['help']

        if '--help' in args or '-h' in args:
            new_cmd_args = ['help'] + cmd_args
            new_args = ['help'] + args

            cmd_args = []
            args = []

            for arg in new_cmd_args:
                if arg not in ('--help', '-h'):
                    cmd_args.append(arg)
            for arg in new_args:
                if arg not in ('--help', '-h'):
                    args.append(arg)

        if args[0] == 'help':
            self.nikola.init_plugins(commands_only=True)
        elif args[0] == 'plugin':
            self.nikola.init_plugins(load_all=True)
        else:
            self.nikola.init_plugins()

        sub_cmds = self.get_cmds()

        if any(arg in ("--version", '-V') for arg in args):
            cmd_args = ['version']
            args = ['version']
        if args[0] not in sub_cmds.keys():
            LOGGER.error("Unknown command {0}".format(args[0]))
            sugg = defaultdict(list)
            sub_filtered = (i for i in sub_cmds.keys() if i != 'run')
            for c in sub_filtered:
                d = levenshtein(c, args[0])
                sugg[d].append(c)
            if sugg.keys():
                best_sugg = sugg[min(sugg.keys())]
                if len(best_sugg) == 1:
                    LOGGER.info('Did you mean "{}"?'.format(best_sugg[0]))
                else:
                    LOGGER.info('Did you mean "{}" or "{}"?'.format('", "'.join(best_sugg[:-1]), best_sugg[-1]))
            return 3

        if not sub_cmds[args[0]] in (Help, TabCompletion) and not isinstance(sub_cmds[args[0]], Command):
            if not self.nikola.configured:
                LOGGER.error("This command needs to run inside an "
                             "existing Nikola site.")
                return 3
        return super(DoitNikola, self).run(cmd_args)

    @staticmethod
    def print_version():
        """Print Nikola version."""
        print("Nikola v" + __version__)


def levenshtein(s1, s2):
    u"""Calculate the Levenshtein distance of two strings.

    Implementation from Wikibooks:
    https://en.wikibooks.org/w/index.php?title=Algorithm_Implementation/Strings/Levenshtein_distance&oldid=2974448#Python
    Copyright © The Wikibooks contributors (CC BY-SA/fair use citation); edited to match coding style and add an exception.
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer than s2
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
