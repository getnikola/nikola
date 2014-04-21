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
import os
import shutil
import subprocess
import sys

from nikola.plugin_categories import Command
from nikola.plugins.command.check import real_scan_files
from nikola.utils import ask_yesno, get_logger
from nikola.__main__ import main
from nikola import __version__


class CommandGitHubDeploy(Command):
    """ Deploy site to GitHub pages. """
    name = 'github_deploy'

    doc_usage = ''
    doc_purpose = 'deploy the site to GitHub pages'

    logger = None

    _deploy_branch = ''
    _source_branch = ''

    def _execute(self, command, args):

        self.logger = get_logger(
            CommandGitHubDeploy.name, self.site.loghandlers
        )
        self._source_branch = self.site.config.get(
            'GITHUB_SOURCE_BRANCH', 'master'
        )
        self._deploy_branch = self.site.config.get(
            'GITHUB_DEPLOY_BRANCH', 'gh-pages'
        )

        self._ensure_git_repo()

        message = (
            "Make sure you have all source files committed. Anything not "
            "committed, and unknown to Nikola may be lost.  Continue? "
        )

        if not ask_yesno(message, False):
            return

        build = main(['build'])
        if build != 0:
            self.logger.error('Build failed, not deploying to GitHub')
            sys.exit(build)

        only_on_output, _ = real_scan_files(self.site)
        for f in only_on_output:
            os.unlink(f)

        self._checkout_deploy_branch()

        self._copy_output()

        self._commit_and_push()

        return

    def _commit_and_push(self):
        """ Commit all the files and push. """

        deploy = self._deploy_branch
        source = self._source_branch

        source_commit = subprocess.check_output(['git', 'rev-parse', source])
        commit_message = (
            'Nikola auto commit.\n\n'
            'Source commit: %s'
            'Nikola version: %s' % (source_commit, __version__)
        )

        commands = [
            ['git', 'add', '-A'],
            ['git', 'commit', '-m', '%s' % commit_message],
            ['git', 'push', 'origin', '%s:%s' % (deploy, deploy)],
            ['git', 'checkout', '%s' % source],
        ]

        for command in commands:
            self.logger.info("==> {0}".format(command))
            try:
                subprocess.check_call(command)
            except subprocess.CalledProcessError as e:
                self.logger.error(
                    'Failed GitHub deployment — command {0} '
                    'returned {1}'.format(e.cmd, e.returncode)
                )
                sys.exit(e.returncode)

    def _copy_output(self):
        """ Copy all output to the top level directory. """
        output_folder = self.site.config['OUTPUT_FOLDER']
        for each in os.listdir(output_folder):
            if os.path.exists(each):
                if os.path.isdir(each):
                    shutil.rmtree(each)

                else:
                    os.unlink(each)

            shutil.move(os.path.join(output_folder, each), '.')

    def _checkout_deploy_branch(self):
        """ Check out the deploy branch

        Creates an orphan branch if not present.

        """

        deploy = self._deploy_branch

        try:
            command = 'git show-ref --verify --quiet refs/heads/%s' % deploy
            subprocess.check_call(command.split())
        except subprocess.CalledProcessError:
            self._create_orphan_deploy_branch()
        else:
            command = 'git checkout %s' % deploy
            subprocess.check_call(command.split())

    def _create_orphan_deploy_branch(self):
        command = 'git checkout --orphan %s' % self._deploy_branch
        result = subprocess.check_call(command.split())
        if result != 0:
            self.logger.error('Failed to create a deploy branch')
            sys.exit(1)

        result = subprocess.check_call('git rm -rf .'.split())
        if result != 0:
            self.logger.error('Failed to create a deploy branch')
            sys.exit(1)

        with open('.gitignore', 'w') as f:
            f.write('%s\n' % self.site.config['OUTPUT_FOLDER'])
            f.write('%s\n' % self.site.config['CACHE_FOLDER'])
            f.write('*.pyc\n')
            f.write('*.db\n')

        subprocess.check_call('git add .gitignore'.split())
        subprocess.check_call(['git', 'commit', '-m', 'Add .gitignore'])

    def _ensure_git_repo(self):
        """ Ensure that the site is a git-repo.

        Also make sure that a remote with the name 'origin' exists.

        """

        try:
            command = 'git remote'
            remotes = subprocess.check_output(command.split())

        except subprocess.CalledProcessError as e:
            self.logger.notice('github_deploy needs a git repository!')
            sys.exit(e.returncode)

        except OSError as e:
            import errno
            self.logger.error('Running git failed with {0}'.format(e))
            if e.errno == errno.ENOENT:
                self.logger.notice('Is git on the PATH?')
            sys.exit(1)

        else:
            if 'origin' not in remotes:
                self.logger.error('Need a remote called "origin" configured')
                sys.exit(1)
