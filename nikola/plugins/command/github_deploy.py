# -*- coding: utf-8 -*-

# Copyright © 2014-2024 Puneeth Chaganti and others.

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

"""Deploy site to GitHub Pages."""

import os
import subprocess
from textwrap import dedent

from nikola.plugin_categories import Command
from nikola.plugins.command.check import real_scan_files
from nikola.utils import req_missing, clean_before_deployment
from nikola.__main__ import main
from nikola import __version__


def uni_check_output(*args, **kwargs):
    """Run command and return output as Unicode (UTf-8)."""
    o = subprocess.check_output(*args, **kwargs)
    return o.decode('utf-8')


def check_ghp_import_installed():
    """Check if ghp-import is installed."""
    try:
        subprocess.check_output(['ghp-import', '-h'])
    except OSError:
        # req_missing defaults to `python=True` — and it’s meant to be like this.
        # `ghp-import` is installed via pip, but the only way to use it is by executing the script it installs.
        req_missing(['ghp-import'], 'deploy the site to GitHub Pages')


class DeployFailedException(Exception):
    """An internal exception for deployment errors."""

    pass


class CommandGitHubDeploy(Command):
    """Deploy site to GitHub Pages."""

    name = 'github_deploy'

    doc_usage = '[-m COMMIT_MESSAGE]'
    doc_purpose = 'deploy the site to GitHub Pages'
    doc_description = dedent(
        """\
        This command can be used to deploy your site to GitHub Pages. It uses ghp-import to do this task. It also optionally commits to the source branch.

        Configuration help: https://getnikola.com/handbook.html#deploying-to-github"""
    )
    cmd_options = [
        {
            'name': 'commit_message',
            'short': 'm',
            'long': 'message',
            'default': 'Nikola auto commit.',
            'type': str,
            'help': 'Commit message',
        },
    ]

    def _execute(self, options, args):
        """Run the deployment."""
        # Check if ghp-import is installed
        check_ghp_import_installed()

        # Build before deploying
        build = main(['build'])
        if build != 0:
            self.logger.error('Build failed, not deploying to GitHub')
            return build

        # Clean non-target files
        only_on_output, _ = real_scan_files(self.site)
        for f in only_on_output:
            os.unlink(f)

        # Remove drafts and future posts if requested (Issue #2406)
        undeployed_posts = clean_before_deployment(self.site)
        if undeployed_posts:
            self.logger.warning("Deleted {0} posts due to DEPLOY_* settings".format(len(undeployed_posts)))

        # Commit and push
        return self._commit_and_push(options['commit_message'])

    def _run_command(self, command, xfail=False):
        """Run a command that may or may not fail."""
        self.logger.info("==> {0}".format(command))
        try:
            subprocess.check_call(command)
            return 0
        except subprocess.CalledProcessError as e:
            if xfail:
                return e.returncode
            self.logger.error(
                'Failed GitHub deployment -- command {0} '
                'returned {1}'.format(e.cmd, e.returncode)
            )
            raise DeployFailedException(e.returncode)

    def _commit_and_push(self, commit_first_line):
        """Commit all the files and push."""
        source = self.site.config['GITHUB_SOURCE_BRANCH']
        deploy = self.site.config['GITHUB_DEPLOY_BRANCH']
        remote = self.site.config['GITHUB_REMOTE_NAME']
        autocommit = self.site.config['GITHUB_COMMIT_SOURCE']
        try:
            if autocommit:
                commit_message = (
                    '{0}\n\n'
                    'Nikola version: {1}'.format(commit_first_line, __version__)
                )
                e = self._run_command(['git', 'checkout', source], True)
                if e != 0:
                    self._run_command(['git', 'checkout', '-b', source])
                self._run_command(['git', 'add', '.'])
                # Figure out if there is anything to commit
                e = self._run_command(['git', 'diff-index', '--quiet', 'HEAD'], True)
                if e != 0:
                    self._run_command(['git', 'commit', '-am', commit_message])
                else:
                    self.logger.info('Nothing to commit to source branch.')

            try:
                source_commit = uni_check_output(['git', 'rev-parse', source])
            except subprocess.CalledProcessError:
                try:
                    source_commit = uni_check_output(['git', 'rev-parse', 'HEAD'])
                except subprocess.CalledProcessError:
                    source_commit = '?'

            commit_message = (
                '{0}\n\n'
                'Source commit: {1}'
                'Nikola version: {2}'.format(commit_first_line, source_commit, __version__)
            )
            output_folder = self.site.config['OUTPUT_FOLDER']

            command = ['ghp-import', '-n', '-m', commit_message, '-p', '-r', remote, '-b', deploy, output_folder]

            self._run_command(command)

            if autocommit:
                self._run_command(['git', 'push', '-u', remote, source])
        except DeployFailedException as e:
            return e.args[0]

        self.logger.info("Successful deployment")
