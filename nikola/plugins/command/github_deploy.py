# -*- coding: utf-8 -*-

# Copyright © 2014 Puneeth Chaganti and others.

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

from __future__ import print_function
import sys
import subprocess

from nikola.plugin_categories import Command
from nikola.utils import get_logger


class CommandGitHubDeploy(Command):
    """ Deploy site to GitHub pages. """
    name = 'github-deploy'

    doc_usage = ''
    doc_purpose = 'deploy the site to GitHub pages'

    logger = None

    def _execute(self, command, args):

        message = (
            "Make sure you have all source files committed. Anything not "
            "committed, and unknown to Nikola may be lost.  Do you want to "
            "continue? (y/N) "
        )

        if not raw_input(message).lower().startswith('y'):
            return

        self.logger = get_logger(
            CommandGitHubDeploy.name, self.site.loghandlers
        )

        commands = [
            'nikola build',
            'nikola check -f --clean-files || true',
            'git checkout --orphan gh-pages',
            'git rm -rf .',
            'git checkout master -- .gitignore',
            'mv output/* .',
            'git add -A',
            'git commit -m "$(date)"',
            'git push -f origin gh-pages:gh-pages',
            'git checkout master',
            'git branch -D gh-pages',
            'git push origin master',
        ]

        for command in commands:
            self.logger.info("==> {0}".format(command))
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError as e:
                self.logger.error('Failed deployment — command {0} '
                                  'returned {1}'.format(e.cmd, e.returncode))
                sys.exit(e.returncode)

        return
