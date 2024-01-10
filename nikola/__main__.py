# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

import importlib.util
import os
import shutil
import sys
import textwrap
import traceback
import doit.cmd_base
from collections import defaultdict

from blinker import signal
from doit.cmd_base import TaskLoader2, _wrap
from doit.cmd_clean import Clean as DoitClean
from doit.cmd_completion import TabCompletion
from doit.cmd_help import Help as DoitHelp
from doit.cmd_run import Run as DoitRun
from doit.doit_cmd import DoitMain
from doit.loader import generate_tasks
from doit.reporter import ExecutedOnlyReporter

from . import __version__
from .nikola import Nikola
from .plugin_categories import Command
from .log import configure_logging, LOGGER, ColorfulFormatter, LoggingMode
from .utils import get_root_dir, req_missing, sys_decode

try:
    import readline  # NOQA
except ImportError:
    pass  # This is only so raw_input/input does nicer things if it's available


config = {}

# DO NOT USE unless you know what you are doing!
_RETURN_DOITNIKOLA = False


def main(args=None):
    """Run Nikola."""
    colorful = False
    if sys.stderr.isatty() and os.name != 'nt' and os.getenv('NIKOLA_MONO') is None and os.getenv('TERM') != 'dumb':
        colorful = True

    ColorfulFormatter._colorful = colorful

    if args is None:
        args = sys.argv[1:]

    oargs = args
    args = [sys_decode(arg) for arg in args]

    conf_filename = 'conf.py'
    conf_filename_changed = False
    for index, arg in enumerate(args):
        if arg[:7] == '--conf=':
            del args[index]
            del oargs[index]
            conf_filename = arg[7:]
            conf_filename_changed = True
            break

    quiet = False
    if len(args) > 0 and args[0] == 'build' and '--strict' in args:
        LOGGER.info('Running in strict mode')
        configure_logging(LoggingMode.STRICT)
    elif len(args) > 0 and args[0] == 'build' and '-q' in args or '--quiet' in args:
        configure_logging(LoggingMode.QUIET)
        quiet = True
    else:
        configure_logging()

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
        LOGGER.debug("Website root: %r", root)
    else:
        needs_config_file = False

    sys.path.insert(0, os.path.dirname(conf_filename))
    try:
        spec = importlib.util.spec_from_file_location("conf", conf_filename)
        conf = importlib.util.module_from_spec(spec)
        # Preserve caching behavior of `import conf` if the filename matches
        if os.path.splitext(os.path.basename(conf_filename))[0] == "conf":
            sys.modules["conf"] = conf
        spec.loader.exec_module(conf)
        config = conf.__dict__
    except Exception:
        if os.path.exists(conf_filename):
            msg = traceback.format_exc()
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
        if os.path.isdir('plugins') and not os.path.exists('plugins/__init__.py'):
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
        super().__init__(*args, **kw)


class Clean(DoitClean):
    """Clean site, including the cache directory."""

    # The unseemly *a is because this API changed between doit 0.30.1 and 0.31
    def clean_tasks(self, tasks, dryrun, *a):
        """Clean tasks."""
        if not dryrun and config:
            cache_folder = config.get('CACHE_FOLDER', 'cache')
            if os.path.exists(cache_folder):
                shutil.rmtree(cache_folder)
        return super(Clean, self).clean_tasks(tasks, dryrun, *a)


# Nikola has its own "auto" commands that uses livereload.
# Expose original doit "auto" command as "doit_auto".
# doit_auto is not available with doit>=0.36.0.
try:
    from doit.cmd_auto import Auto as DoitAuto
    DoitAuto.name = 'doit_auto'
except ImportError:
    DoitAuto = None


class NikolaTaskLoader(TaskLoader2):
    """Nikola-specific task loader."""

    def __init__(self, nikola, quiet=False):
        """Initialize the loader."""
        super().__init__()
        self.nikola = nikola
        self.quiet = quiet

    def load_doit_config(self):
        """Load doit configuration."""
        if self.quiet:
            doit_config = {
                'verbosity': 0,
                'reporter': 'zero',
            }
        else:
            doit_config = {
                'reporter': ExecutedOnlyReporter,
                'outfile': sys.stderr,
            }
        doit_config['default_tasks'] = ['render_site', 'post_render']
        doit_config.update(self.nikola._doit_config)
        return doit_config

    def load_tasks(self, cmd, pos_args):
        """Load Nikola tasks."""
        try:
            tasks = generate_tasks(
                'render_site',
                self.nikola.gen_tasks('render_site', "Task", 'Group of tasks to render the site.'))
            latetasks = generate_tasks(
                'post_render',
                self.nikola.gen_tasks('post_render', "LateTask", 'Group of tasks to be executed after site is rendered.'))
            signal('initialized').send(self.nikola)
        except Exception:
            LOGGER.error('Error loading tasks. An unhandled exception occurred.')
            if self.nikola.debug or self.nikola.show_tracebacks:
                raise
            _print_exception()
            sys.exit(3)
        return tasks + latetasks


class DoitNikola(DoitMain):
    """Nikola-specific implementation of DoitMain."""

    # overwite help command
    DOIT_CMDS = list(DoitMain.DOIT_CMDS) + [Help, Build, Clean]
    TASK_LOADER = NikolaTaskLoader
    if DoitAuto is not None:
        DOIT_CMDS.append(DoitAuto)

    def __init__(self, nikola, quiet=False):
        """Initialzie DoitNikola."""
        super().__init__()
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
        try:
            return super().run(cmd_args)
        except Exception:
            LOGGER.error('An unhandled exception occurred.')
            if self.nikola.debug or self.nikola.show_tracebacks:
                raise
            _print_exception()
            return 1

    @staticmethod
    def print_version():
        """Print Nikola version."""
        print("Nikola v" + __version__)


# Override Command.help() to make it more readable and to remove
# some doit-specific stuff. Based on doit's implementation.
# (see Issue #3342)
def _command_help(self: Command):
    """Return help text for a command."""
    text = []

    usage = "{} {} {}".format(self.bin_name, self.name, self.doc_usage)
    text.extend(textwrap.wrap(usage, subsequent_indent='  '))
    text.extend(_wrap(self.doc_purpose, 4))

    text.append("\nOptions:")
    options = defaultdict(list)
    for opt in self.cmdparser.options:
        options[opt.section].append(opt)
    for section, opts in sorted(options.items()):
        if section:
            section_name = '\n{}'.format(section)
            text.extend(_wrap(section_name, 2))
        for opt in opts:
            # ignore option that cant be modified on cmd line
            if not (opt.short or opt.long):
                continue
            text.extend(_wrap(opt.help_param(), 4))
            opt_help = opt.help
            if '%(default)s' in opt_help:
                opt_help = opt.help % {'default': opt.default}
            elif opt.default != '' and opt.default is not False and opt.default is not None:
                opt_help += ' [default: {}]'.format(opt.default)
            opt_choices = opt.help_choices()
            desc = '{} {}'.format(opt_help, opt_choices)
            text.extend(_wrap(desc, 8))

            # print bool inverse option
            if opt.inverse:
                text.extend(_wrap('--{}'.format(opt.inverse), 4))
                text.extend(_wrap('opposite of --{}'.format(opt.long), 8))

    if self.doc_description is not None:
        text.append("\n\nDescription:")
        text.extend(_wrap(self.doc_description, 4))
    return "\n".join(text)


doit.cmd_base.Command.help = _command_help


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


def _print_exception():
    """Print an exception in a friendlier, shorter style."""
    etype, evalue, _ = sys.exc_info()
    LOGGER.error(''.join(traceback.format_exception(etype, evalue, None, limit=0, chain=False)).strip())
    LOGGER.warning("To see more details, run Nikola in debug mode (set environment variable NIKOLA_DEBUG=1) or use NIKOLA_SHOW_TRACEBACKS=1")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
