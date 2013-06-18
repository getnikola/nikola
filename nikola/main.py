# -*- coding: utf-8 -*-
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
import sys
from operator import attrgetter

from doit.loader import generate_tasks
from doit.cmd_base import TaskLoader
from doit.reporter import ExecutedOnlyReporter
from doit.doit_cmd import DoitMain
from doit.cmd_help import Help as DoitHelp
from doit.cmd_run import Run as DoitRun

from .nikola import Nikola
from .utils import _reload, sys_decode

VERSION = "5.4.4"


def main(args):
    sys.path.append('')
    try:
        import conf
        _reload(conf)
        config = conf.__dict__
    except ImportError:
        config = {}

    site = Nikola(**config)
    return DoitNikola(site).run(args)


class Help(DoitHelp):
    """show Nikola usage instead of doit """

    @staticmethod
    def print_usage(cmds):
        """print nikola "usage" (basic help) instructions"""
        print("Nikola is a tool to create static websites and blogs. For full documentation and more information, please visit http://nikola.ralsina.com.ar\n\n")
        print("Available commands:")
        for cmd in sorted(cmds.values(), key=attrgetter('name')):
            print("  nikola %s \t\t %s" % (cmd.name, cmd.doc_purpose))
        print("")
        print("  nikola help              show help / reference")
        print("  nikola help <command>    show command usage")
        print("  nikola help <task-name>  show task usage")


class Build(DoitRun):
    """expose "run" command as "build" for backward compatibility"""
    pass


class NikolaTaskLoader(TaskLoader):
    """custom task loader to get tasks from Nikola instead of dodo.py file"""
    def __init__(self, nikola):
        self.nikola = nikola

    def load_tasks(self, cmd, opt_values, pos_args):
        DOIT_CONFIG = {
            'reporter': ExecutedOnlyReporter,
            'default_tasks': ['render_site', 'post_render'],
        }
        tasks = generate_tasks('render_site', self.nikola.gen_tasks('render_site', "Task"))
        latetasks = generate_tasks('post_render', self.nikola.gen_tasks('post_render', "LateTask"))
        return tasks + latetasks, DOIT_CONFIG


class DoitNikola(DoitMain):
    # overwite help command
    DOIT_CMDS = list(DoitMain.DOIT_CMDS) + [Help, Build]
    TASK_LOADER = NikolaTaskLoader

    def __init__(self, nikola):
        self.nikola = nikola
        self.task_loader = self.TASK_LOADER(nikola)

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

        if len(args) == 0 or args[0] not in sub_cmds.keys() or \
                args[0] in ('run', 'build'):
            # Check for conf.py before launching run
            if not self.nikola.configured:
                print("This command needs to run inside an "
                      "existing Nikola site.")
                return False
        super(DoitNikola, self).run(cmd_args)

    @staticmethod
    def print_version():
        print("Nikola version %s" % VERSION)
