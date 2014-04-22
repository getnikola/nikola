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
from textwrap import dedent

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
    doc_description = dedent(
        """\
        This command can be used to deploy your site to GitHub pages.
        It performs the following actions:

        1. Ensure that your site is a git repository, and git is on the PATH.
        2. Check for changes, and prompt the user to continue, if required.
        3. Build the site
        4. Clean any files that are "unknown" to Nikola.
        5. Create a deploy branch, if one doesn't exist.
        6. Commit the output to this branch.  (NOTE: Any untracked source
           files, may get committed at this stage, on the wrong branch!)
        7. Push and deploy!

        NOTE: This command needs your site to be a git repository, with a
        master branch (or a different branch, configured using
        GITHUB_SOURCE_BRANCH if you are pushing to user.github
        .io/organization.github.io pages) containing the sources of your
        site.  You also, obviously, need to have `git` on your PATH,
        and should be able to push to the repository specified as the remote
        (origin, by default).
        """
    )

    logger = None

    _deploy_branch = ''
    _source_branch = ''
    _remote_name = ''

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
        self._remote_name = self.site.config.get(
            'GITHUB_REMOTE_NAME', 'origin'
        )

        self._ensure_git_repo()

        if not self._prompt_continue():
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
        remote = self._remote_name

        source_commit = subprocess.check_output(['git', 'rev-parse', source])
        commit_message = (
            'Nikola auto commit.\n\n'
            'Source commit: %s'
            'Nikola version: %s' % (source_commit, __version__)
        )

        commands = [
            ['git', 'add', '-A'],
            ['git', 'commit', '-m', commit_message],
            ['git', 'push', '-f', remote, '%s:%s' % (deploy, deploy)],
            ['git', 'checkout', source],
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
            subprocess.check_call(
                [
                    'git', 'show-ref', '--verify', '--quiet',
                    'refs/heads/%s' % deploy
                ]
            )
        except subprocess.CalledProcessError:
            self._create_orphan_deploy_branch()
        else:
            subprocess.check_call(['git', 'checkout', deploy])

    def _create_orphan_deploy_branch(self):
        """ Create an orphan deploy branch """

        result = subprocess.check_call(
            ['git', 'checkout', '--orphan', self._deploy_branch]
        )
        if result != 0:
            self.logger.error('Failed to create a deploy branch')
            sys.exit(1)

        result = subprocess.check_call(['git', 'rm', '-rf', '.'])
        if result != 0:
            self.logger.error('Failed to create a deploy branch')
            sys.exit(1)

        with open('.gitignore', 'w') as f:
            f.write('%s\n' % self.site.config['OUTPUT_FOLDER'])
            f.write('%s\n' % self.site.config['CACHE_FOLDER'])
            f.write('*.pyc\n')
            f.write('*.db\n')

        subprocess.check_call(['git', 'add', '.gitignore'])
        subprocess.check_call(['git', 'commit', '-m', 'Add .gitignore'])

    def _ensure_git_repo(self):
        """ Ensure that the site is a git-repo.

        Also make sure that a remote with the specified name exists.

        """

        try:
            remotes = subprocess.check_output(['git', 'remote'])

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
            if self._remote_name not in remotes:
                self.logger.error(
                    'Need a remote called "%s" configured' % self._remote_name
                )
                sys.exit(1)

    def _prompt_continue(self):
        """ Show uncommitted changes, and ask if user wants to continue. """

        changes = subprocess.check_output(['git', 'status', '--porcelain'])
        if changes.strip():
            changes = subprocess.check_output(['git', 'status']).strip()
            message = (
                "You have the following changes:\n%s\n\n"
                "Anything not committed, and unknown to Nikola may be lost, "
                "or committed onto the wrong branch. Do you wish to continue?"
            ) % changes
            proceed = ask_yesno(message, False)

        else:
            proceed = True

        return proceed
