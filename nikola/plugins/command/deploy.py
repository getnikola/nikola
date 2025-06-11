# -*- coding: utf-8 -*-

# Copyright © 2012-2025 Roberto Alsina and others.

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

import subprocess
import time
from datetime import datetime

import dateutil
from blinker import signal
from dateutil.tz import gettz

from nikola.plugin_categories import Command
from nikola.utils import clean_before_deployment


class CommandDeploy(Command):
    """Deploy site."""

    name = "deploy"

    doc_usage = "[preset [preset...]]"
    doc_purpose = "deploy the site"
    doc_description = "Deploy the site by executing deploy commands from the presets listed on the command line.  If no presets are specified, `default` is executed."

    def _execute(self, command, args):
        """Execute the deploy command."""
        # Get last-deploy from persistent state
        last_deploy = self.site.state.get('last_deploy')
        if last_deploy is not None:
            last_deploy = dateutil.parser.parse(last_deploy)
            clean = False
        else:
            clean = True

        if self.site.config['COMMENT_SYSTEM'] and self.site.config['COMMENT_SYSTEM_ID'] == 'nikolademo':
            self.logger.warning("\nWARNING WARNING WARNING WARNING\n"
                                "You are deploying using the nikolademo Disqus account.\n"
                                "That means you will not be able to moderate the comments in your own site.\n"
                                "And is probably not what you want to do.\n"
                                "Think about it for 5 seconds, I'll wait :-)\n"
                                "(press Ctrl+C to abort)\n")
            time.sleep(5)

        # Remove drafts and future posts if requested
        undeployed_posts = clean_before_deployment(self.site)
        if undeployed_posts:
            self.logger.warning(f"Deleted {len(undeployed_posts)} posts due to DEPLOY_* settings")

        if args:
            presets = args
        else:
            presets = ['default']

        # test for preset existence
        for preset in presets:
            try:
                self.site.config['DEPLOY_COMMANDS'][preset]
            except KeyError:
                self.logger.error(f'No such preset: {preset}')
                return 255

        for preset in presets:
            self.logger.info(f"=> preset '{preset}'")
            for command in self.site.config['DEPLOY_COMMANDS'][preset]:
                self.logger.info(f"==> {command}")
                try:
                    subprocess.check_call(command, shell=True)
                except subprocess.CalledProcessError as e:
                    self.logger.error(f'Failed deployment -- command {e.cmd} '
                                      f'returned {e.returncode}')
                    return e.returncode

        self.logger.info("Successful deployment")

        new_deploy = datetime.utcnow()
        if last_deploy is None:
            last_deploy = new_deploy
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
