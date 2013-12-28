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

from __future__ import print_function
from ast import literal_eval
import codecs
from datetime import datetime
import os
import sys
import subprocess
import time
import pytz

from blinker import signal

from nikola.plugin_categories import Command
from nikola.utils import remove_file, get_logger


class Deploy(Command):
    """Deploy site.  """
    name = "deploy"

    doc_usage = ""
    doc_purpose = "deploy the site"

    logger = None

    def _execute(self, command, args):
        self.logger = get_logger('deploy', self.site.loghandlers)
        # Get last successful deploy date
        timestamp_path = os.path.join(self.site.config['CACHE_FOLDER'], 'lastdeploy')
        if self.site.config['COMMENT_SYSTEM_ID'] == 'nikolademo':
            self.logger.warn("\nWARNING WARNING WARNING WARNING\n"
                             "You are deploying using the nikolademo Disqus account.\n"
                             "That means you will not be able to moderate the comments in your own site.\n"
                             "And is probably not what you want to do.\n"
                             "Think about it for 5 seconds, I'll wait :-)\n\n")
            time.sleep(5)

        deploy_drafts = self.site.config.get('DEPLOY_DRAFTS', True)
        deploy_future = self.site.config.get('DEPLOY_FUTURE', False)
        if not (deploy_drafts and deploy_future):
            # Remove drafts and future posts
            out_dir = self.site.config['OUTPUT_FOLDER']
            undeployed_posts = []
            self.site.scan_posts()
            for post in self.site.timeline:
                if (not deploy_drafts and post.is_draft) or \
                   (not deploy_future and post.publish_later):
                    remove_file(os.path.join(out_dir, post.destination_path()))
                    remove_file(os.path.join(out_dir, post.source_path))
                    undeployed_posts.append(post)

        for command in self.site.config['DEPLOY_COMMANDS']:
            self.logger.notice("==> {0}".format(command))
            try:
                subprocess.check_call(command, shell=True)
            except subprocess.CalledProcessError as e:
                self.logger.error('Failed deployment — command {0} '
                                  'returned {1}'.format(e.cmd, e.returncode))
                sys.exit(e.returncode)

        self.logger.notice("Successful deployment")
        tzinfo = pytz.timezone(self.site.config['TIMEZONE'])
        try:
            with open(timestamp_path, 'rb') as inf:
                last_deploy = literal_eval(inf.read().strip())
                if tzinfo:
                    last_deploy = last_deploy.replace(tzinfo=tzinfo)
                clean = False
        except Exception:
            last_deploy = datetime(1970, 1, 1)
            if tzinfo:
                last_deploy = last_deploy.replace(tzinfo=tzinfo)
            clean = True

        new_deploy = datetime.now()
        self._emit_deploy_event(last_deploy, new_deploy, clean, undeployed_posts)

        # Store timestamp of successful deployment
        with codecs.open(timestamp_path, 'wb+', 'utf8') as outf:
            outf.write(repr(new_deploy))

    def _emit_deploy_event(self, last_deploy, new_deploy, clean=False, undeployed=None):
        """ Emit events for all timeline entries newer than last deploy.

        last_deploy: datetime
            Time stamp of the last successful deployment.

        new_deploy: datetime
            Time stamp of the current deployment.

        clean: bool
            True when it appears like deploy is being run after a clean.

        """

        if undeployed is None:
            undeployed = []

        event = {
            'last_deploy': last_deploy,
            'new_deploy': new_deploy,
            'clean': clean,
            'undeployed': undeployed
        }

        deployed = [
            entry for entry in self.site.timeline
            if entry.date > last_deploy and entry not in undeployed
        ]

        event['deployed'] = deployed

        if len(deployed) > 0 or len(undeployed) > 0:
            signal('deployed').send(event)
