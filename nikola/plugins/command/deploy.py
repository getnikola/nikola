# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Deploy site."""

from __future__ import print_function
import io
from datetime import datetime
from dateutil.tz import gettz
import dateutil
import os
import subprocess
import time

from blinker import signal

from nikola.plugin_categories import Command
from nikola.utils import get_logger, clean_before_deployment, STDERR_HANDLER


class CommandDeploy(Command):
    """Deploy site."""

    name = "deploy"

    doc_usage = "[preset [preset...]]"
    doc_purpose = "deploy the site"
    doc_description = "Deploy the site by executing deploy commands from the presets listed on the command line.  If no presets are specified, `default` is executed."
    logger = None

    def _execute(self, command, args):
        """Execute the deploy command."""
        self.logger = get_logger('deploy', STDERR_HANDLER)
        # Get last successful deploy date
        timestamp_path = os.path.join(self.site.config['CACHE_FOLDER'], 'lastdeploy')

        # Get last-deploy from persistent state
        last_deploy = self.site.state.get('last_deploy')
        if last_deploy is None:
            # If there is a last-deploy saved, move it to the new state persistence thing
            # FIXME: remove in Nikola 8
            if os.path.isfile(timestamp_path):
                try:
                    with io.open(timestamp_path, 'r', encoding='utf8') as inf:
                        last_deploy = dateutil.parser.parse(inf.read())
                        clean = False
                except (IOError, Exception) as e:
                    self.logger.debug("Problem when reading `{0}`: {1}".format(timestamp_path, e))
                    last_deploy = datetime(1970, 1, 1)
                    clean = True
                os.unlink(timestamp_path)  # Remove because from now on it's in state
            else:  # Just a default
                last_deploy = datetime(1970, 1, 1)
                clean = True
        else:
            last_deploy = dateutil.parser.parse(last_deploy)
            clean = False

        if self.site.config['COMMENT_SYSTEM'] and self.site.config['COMMENT_SYSTEM_ID'] == 'nikolademo':
            self.logger.warn("\nWARNING WARNING WARNING WARNING\n"
                             "You are deploying using the nikolademo Disqus account.\n"
                             "That means you will not be able to moderate the comments in your own site.\n"
                             "And is probably not what you want to do.\n"
                             "Think about it for 5 seconds, I'll wait :-)\n"
                             "(press Ctrl+C to abort)\n")
            time.sleep(5)

        # Remove drafts and future posts if requested
        undeployed_posts = clean_before_deployment(self.site)
        if undeployed_posts:
            self.logger.notice("Deleted {0} posts due to DEPLOY_* settings".format(len(undeployed_posts)))

        if args:
            presets = args
        else:
            presets = ['default']

        # test for preset existence
        for preset in presets:
            try:
                self.site.config['DEPLOY_COMMANDS'][preset]
            except:
                self.logger.error('No such preset: {0}'.format(preset))
                return 255

        for preset in presets:
            self.logger.info("=> preset '{0}'".format(preset))
            for command in self.site.config['DEPLOY_COMMANDS'][preset]:
                self.logger.info("==> {0}".format(command))
                try:
                    subprocess.check_call(command, shell=True)
                except subprocess.CalledProcessError as e:
                    self.logger.error('Failed deployment -- command {0} '
                                      'returned {1}'.format(e.cmd, e.returncode))
                    return e.returncode

        self.logger.info("Successful deployment")

        new_deploy = datetime.utcnow()
        self._emit_deploy_event(last_deploy, new_deploy, clean, undeployed_posts)

        # Store timestamp of successful deployment
        self.site.state.set('last_deploy', new_deploy.isoformat())
        if clean:
            self.logger.info(
                'Looks like this is the first time you deployed this site. '
                'Let us know you are using Nikola '
                'at <https://users.getnikola.com/add/> if you want!')

    def _emit_deploy_event(self, last_deploy, new_deploy, clean=False, undeployed=None):
        """Emit events for all timeline entries newer than last deploy.

        last_deploy: datetime
            Time stamp of the last successful deployment.

        new_deploy: datetime
            Time stamp of the current deployment.

        clean: bool
            True when it appears like deploy is being run after a clean.

        """
        event = {
            'last_deploy': last_deploy,
            'new_deploy': new_deploy,
            'clean': clean,
            'undeployed': undeployed
        }

        if last_deploy.tzinfo is None:
            last_deploy = last_deploy.replace(tzinfo=gettz('UTC'))

        deployed = [
            entry for entry in self.site.timeline
            if entry.date > last_deploy and entry not in undeployed
        ]

        event['deployed'] = deployed

        if len(deployed) > 0 or len(undeployed) > 0:
            signal('deployed').send(event)
