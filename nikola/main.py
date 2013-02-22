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

from doit.loader import generate_tasks
from doit.cmd_base import TaskLoader
from doit.reporter import ExecutedOnlyReporter
from doit.doit_cmd import DoitMain

from .nikola import Nikola


def main():
    try:
        sys.path.append('')
        import conf
        config = conf.__dict__
    except ImportError:
        config = {}

    site = Nikola(**config)
    DoitNikola(site).run(sys.argv[1:])


def print_help(site):
    print("Usage: nikola command [options]")
    print()
    print("Available commands:")
    print()
    keys = sorted(site.commands.keys())
    for name in keys:
        print("nikola %s: %s" % (name, site.commands[name].short_help))
    print()
    print("For detailed help for a command, use nikola command --help")


class NikolaTaskLoader(TaskLoader):
    """custom task loader to get tasks from Nikola instead of dodo.py file"""
    def __init__(self, nikola):
        self.nikola = nikola

    def load_tasks(self, cmd, opt_values, pos_args):
        DOIT_CONFIG = {
            'reporter': ExecutedOnlyReporter,
            'default_tasks': ['render_site'],
        }
        tasks = generate_tasks('render_site', self.nikola.gen_tasks())
        return tasks, DOIT_CONFIG


class DoitNikola(DoitMain):
    TASK_LOADER = NikolaTaskLoader

    def __init__(self, nikola):
        self.nikola = nikola
        self.task_loader = self.TASK_LOADER(nikola)

    def get_commands(self):
        # core doit commands
        cmds = DoitMain.get_commands(self)

        # load nikola commands
        for name, cmd in self.nikola.commands.iteritems():
            cmds[name] = cmd
        return cmds
