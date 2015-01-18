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
from doit.cmd_auto import Auto as DoitAuto
from doit.task import Task, DelayedLoader
from logbook import NullHandler
from blinker import signal

from . import __version__
from .plugin_categories import Command
from .nikola import Nikola
from .utils import sys_decode, sys_encode, get_root_dir, req_missing, LOGGER, STRICT_HANDLER, ColorfulStderrHandler

if sys.version_info[0] == 3:
    import importlib.machinery
else:
    import imp

config = {}

# DO NOT USE unless you know what you are doing!
_RETURN_DOITNIKOLA = False


def main(args=None):
    colorful = False
    if sys.stderr.isatty() and os.name != 'nt':
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
    if len(args) > 0 and args[0] == 'build' and '--strict' in args:
        LOGGER.notice('Running in strict mode')
        STRICT_HANDLER.push_application()
    if len(args) > 0 and args[0] == 'build' and '-q' in args or '--quiet' in args:
        nullhandler = NullHandler()
        nullhandler.push_application()
        quiet = True
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
        # help does not need a config file, but can use one.
        needs_config_file = argname != 'help'
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
            sys.exit(1)
        elif needs_config_file and conf_filename_changed:
            LOGGER.error('Cannot find configuration file "{0}".'.format(conf_filename))
            sys.exit(1)
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
    """show Nikola usage."""

    @staticmethod
    def print_usage(cmds):
        """print nikola "usage" (basic help) instructions"""
        # Remove 'run'.  Nikola uses 'build', though we support 'run' for
        # people used to it (eg. doit users).
        # WARNING: 'run' is the vanilla doit command, without support for
        #          --strict, --invariant and --quiet.
        del cmds['run']

        print("Nikola is a tool to create static websites and blogs. For full documentation and more information, please visit http://getnikola.com/\n\n")
        print("Available commands:")
        for cmd_name in sorted(cmds.keys()):
            cmd = cmds[cmd_name]
            print("  nikola {:20s} {}".format(cmd_name, cmd.doc_purpose))
        print("")
        print("  nikola help                 show help / reference")
        print("  nikola help <command>       show command usage")
        print("  nikola help <task-name>     show task usage")


class Build(DoitRun):
    """expose "run" command as "build" for backward compatibility"""
    def __init__(self, *args, **kw):
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
    """A clean that removes cache/"""

    def clean_tasks(self, tasks, dryrun):
        if not dryrun and config:
            cache_folder = config.get('CACHE_FOLDER', 'cache')
            if os.path.exists(cache_folder):
                shutil.rmtree(cache_folder)
        return super(Clean, self).clean_tasks(tasks, dryrun)

# Nikola has its own "auto" commands that uses livereload.
# Expose original doit "auto" command as "doit_auto".
DoitAuto.name = 'doit_auto'


class NikolaTaskLoader(TaskLoader):
    """custom task loader to get tasks from Nikola instead of dodo.py file"""
    def __init__(self, nikola, quiet=False):
        self.nikola = nikola
        self.quiet = quiet

    def _get_stage_info(self, stage):
        if stage == -10:
            post_name = 'pre_scanning'
            pre_name = 'pre_scanning_pre'
            doc = 'Group of tasks to be run before scanning for posts'
        elif stage == 0:
            post_name = 'scanning'
            pre_name = 'scanning_pre'
            doc = 'Task scanning for posts'
        elif stage == 10:
            post_name = 'render_site'
            pre_name = 'render_site_pre'
            doc = 'Group of tasks to render the site.'
        elif stage == 100:
            post_name = 'post_render'
            pre_name = 'post_render_pre'
            doc = 'Group of tasks to be executed after site is rendered.'
        else:
            post_name = 'stage_{0}_done'.format(stage)
            pre_name = 'stage_{0}_pre'.format(stage)
            doc = 'Stage {0} tasks'.format(stage)
        return pre_name, post_name, doc

    def _add_task_dep(self, task, dep):
        if 'task_dep' not in task:
            task['task_dep'] = []
        task['task_dep'].append(dep)

    def _generate_plugin_task(self, plugin_object, post_name):
        tasks, task_dep_ = self.nikola.gen_task(post_name, plugin_object)
        for task in tasks:
            yield task
        yield {
            'basename': plugin_object.name,
            'name': 'base_task[{0}]'.format(plugin_object.name),
            'doc': 'Base task for {0}'.format(plugin_object.name),
            'task_dep': task_dep_,
            'actions': None,
        }

    def _generate_plugin_generator_task(self, plugin_object, pre_name, post_name):
        return Task(plugin_object.name, None, loader=DelayedLoader(lambda: self._generate_plugin_task(plugin_object, post_name), executed=pre_name))

    def _generate_stage_tasks(self, stage, previous_stage=None, make_delayed=False):
        pre_name, post_name, doc = self._get_stage_info(stage)
        pre_task = {
            'basename': pre_name,
            'name': None,
            'doc': 'Initial waiting task for tasks in group "{0}"'.format(post_name),
            'clean': True,
        }
        if previous_stage is not None:
            _, last_post_name, _ = self._get_stage_info(previous_stage)
            pre_task['task_dep'] = [last_post_name]
        yield pre_task

        task_dep = []
        for plugin_object in self.nikola.get_stage_plugin_objects(stage):
            this_task_deps = [plugin_object.name]
            if make_delayed:
                yield self._generate_plugin_generator_task(plugin_object, pre_name, post_name)
            else:
                tasks, task_dep_ = self.nikola.gen_task(post_name, plugin_object)
                this_task_deps += task_dep_
                for task in tasks:
                    self._add_task_dep(task, pre_name)
                    yield task
            if plugin_object.is_default:
                task_dep.extend(this_task_deps)

        yield {
            'basename': post_name,
            'name': None,
            'doc': doc,
            'clean': True,
            'task_dep': task_dep
        }

    def load_tasks(self, cmd, opt_values, pos_args):
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
        stages = self.nikola.get_task_stages()
        DOIT_CONFIG['default_tasks'] = []
        DOIT_CONFIG.update(self.nikola._doit_config)
        tasks = []
        previous_stage = None
        for stage in stages:
            _, name, _ = self._get_stage_info(stage)
            DOIT_CONFIG['default_tasks'].append(name)
            tasks.extend(generate_tasks(
                name,
                self._generate_stage_tasks(stage, previous_stage, cmd.execute_tasks and previous_stage is not None)))
            previous_stage = stage
        signal('initialized').send(self.nikola)
        return tasks, DOIT_CONFIG


class DoitNikola(DoitMain):
    # overwite help command
    DOIT_CMDS = list(DoitMain.DOIT_CMDS) + [Help, Build, Clean, DoitAuto]
    TASK_LOADER = NikolaTaskLoader

    def __init__(self, nikola, quiet=False):
        super(DoitNikola, self).__init__()
        self.nikola = nikola
        nikola.doit = self
        self.task_loader = self.TASK_LOADER(nikola, quiet)

    def get_cmds(self):
        # core doit commands
        cmds = DoitMain.get_cmds(self)
        # load nikola commands
        for name, cmd in self.nikola._commands.items():
            cmds[name] = cmd
        return cmds

    def run(self, cmd_args):
        sub_cmds = self.get_cmds()
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

        if any(arg in ("--version", '-V') for arg in args):
            cmd_args = ['version']
            args = ['version']
        if args[0] not in sub_cmds.keys():
            LOGGER.error("Unknown command {0}".format(args[0]))
            return 3
        if sub_cmds[args[0]] is not Help and not isinstance(sub_cmds[args[0]], Command):  # Is a doit command
            if not self.nikola.configured:
                LOGGER.error("This command needs to run inside an "
                             "existing Nikola site.")
                return 3

        return super(DoitNikola, self).run(cmd_args)

    @staticmethod
    def print_version():
        print("Nikola v" + __version__)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
