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
from operator import attrgetter
import os
import shutil
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
from logbook import NullHandler

from . import __version__
from .nikola import Nikola
from .utils import _reload, sys_decode, get_root_dir, LOGGER, STRICT_HANDLER


config = {}


def main(args):
    quiet = False
    if len(args) > 0 and args[0] == 'build' and '--strict' in args:
        LOGGER.notice('Running in strict mode')
        STRICT_HANDLER.push_application()
    if len(args) > 0 and args[0] == 'build' and '-q' in args or '--quiet' in args:
        nullhandler = NullHandler()
        nullhandler.push_application()
        quiet = True
    global config

    root = get_root_dir()
    if root:
        os.chdir(root)

    sys.path.append('')
    try:
        import conf
        _reload(conf)
        config = conf.__dict__
    except Exception:
        if os.path.exists('conf.py'):
            msg = traceback.format_exc(0).splitlines()[1]
            LOGGER.error('In conf.py line {0}: {1}'.format(sys.exc_info()[2].tb_lineno, msg))
            sys.exit(1)
        config = {}

    site = Nikola(**config)
    return DoitNikola(site, quiet).run(args)


class Help(DoitHelp):
    """show Nikola usage instead of doit """

    @staticmethod
    def print_usage(cmds):
        """print nikola "usage" (basic help) instructions"""
        print("Nikola is a tool to create static websites and blogs. For full documentation and more information, please visit http://getnikola.com\n\n")
        print("Available commands:")
        for cmd in sorted(cmds.values(), key=attrgetter('name')):
            print("  nikola %-*s %s" % (20, cmd.name, cmd.doc_purpose))
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

    def load_tasks(self, cmd, opt_values, pos_args):
        if self.quiet:
            DOIT_CONFIG = {
                'verbosity': 0,
                'reporter': 'zero',
            }
        else:
            DOIT_CONFIG = {
                'reporter': ExecutedOnlyReporter,
            }
        DOIT_CONFIG['default_tasks'] = ['render_site', 'post_render']
        tasks = generate_tasks(
            'render_site',
            self.nikola.gen_tasks('render_site', "Task", 'Group of tasks to render the site.'))
        latetasks = generate_tasks(
            'post_render',
            self.nikola.gen_tasks('post_render', "LateTask", 'Group of tasks to be executes after site is rendered.'))
        return tasks + latetasks, DOIT_CONFIG


class DoitNikola(DoitMain):
    # overwite help command
    DOIT_CMDS = list(DoitMain.DOIT_CMDS) + [Help, Build, Clean, DoitAuto]
    TASK_LOADER = NikolaTaskLoader

    def __init__(self, nikola, quiet=False):
        self.nikola = nikola
        self.task_loader = self.TASK_LOADER(nikola, quiet)

    def get_commands(self):
        # core doit commands
        cmds = DoitMain.get_commands(self)
        # load nikola commands
        for name, cmd in self.nikola.commands.items():
            cmds[name] = cmd
        return cmds

    def run(self, cmd_args):
        sub_cmds = self.get_commands()
        args = self.process_args(cmd_args)
        args = [sys_decode(arg) for arg in args]

        if len(args) == 0 or any(arg in ["--help", '-h'] for arg in args):
            cmd_args = ['help']
            args = ['help']
            # Hide run because Nikola uses build
            sub_cmds.pop('run')

        if len(args) == 0 or args[0] not in sub_cmds.keys() or \
                args[0] == 'build':
            # Check for conf.py before launching run
            if not self.nikola.configured:
                LOGGER.error("This command needs to run inside an "
                             "existing Nikola site.")
                return False
        return super(DoitNikola, self).run(cmd_args)

    @staticmethod
    def print_version():
        print("Nikola version " + __version__)
