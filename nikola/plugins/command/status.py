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

"""Display site status."""

import os
from datetime import datetime
from dateutil.tz import gettz, tzlocal

from nikola.plugin_categories import Command


class CommandStatus(Command):
    """Display site status."""

    name = "status"

    doc_purpose = "display site status"
    doc_description = "Show information about the posts and site deployment."
    doc_usage = '[-d|--list-drafts] [-m|--list-modified] [-p|--list-private] [-P|--list-published] [-s|--list-scheduled]'
    logger = None
    cmd_options = [
        {
            'name': 'list_drafts',
            'short': 'd',
            'long': 'list-drafts',
            'type': bool,
            'default': False,
            'help': 'List all drafts',
        },
        {
            'name': 'list_modified',
            'short': 'm',
            'long': 'list-modified',
            'type': bool,
            'default': False,
            'help': 'List all modified files since last deployment',
        },
        {
            'name': 'list_private',
            'short': 'p',
            'long': 'list-private',
            'type': bool,
            'default': False,
            'help': 'List all private posts',
        },
        {
            'name': 'list_published',
            'short': 'P',
            'long': 'list-published',
            'type': bool,
            'default': False,
            'help': 'List all published posts',
        },
        {
            'name': 'list_scheduled',
            'short': 's',
            'long': 'list-scheduled',
            'type': bool,
            'default': False,
            'help': 'List all scheduled posts',
        },
    ]

    def _execute(self, options, args):
        """Display site status."""
        self.site.scan_posts()

        last_deploy = self.site.state.get('last_deploy')
        if last_deploy is not None:
            last_deploy = datetime.strptime(last_deploy, "%Y-%m-%dT%H:%M:%S.%f")
            last_deploy_offset = datetime.utcnow() - last_deploy
        else:
            print("It does not seem like you've ever deployed the site (or cache missing).")

        if last_deploy:

            fmod_since_deployment = []
            for root, dirs, files in os.walk(self.site.config["OUTPUT_FOLDER"], followlinks=True):
                if not dirs and not files:
                    continue
                for fname in files:
                    fpath = os.path.join(root, fname)
                    fmodtime = datetime.fromtimestamp(os.stat(fpath).st_mtime)
                    if fmodtime.replace(tzinfo=tzlocal()) > last_deploy.replace(tzinfo=gettz("UTC")).astimezone(tz=tzlocal()):
                        fmod_since_deployment.append(fpath)

            if len(fmod_since_deployment) > 0:
                print(f"{str(len(fmod_since_deployment))} output files modified since last deployment {self.human_time(last_deploy_offset)} ago.")
                if options['list_modified']:
                    for fpath in fmod_since_deployment:
                        print(f"Modified: '{fpath}'")
            else:
                print(f"Last deployment {self.human_time(last_deploy_offset)} ago.")

        now = datetime.utcnow().replace(tzinfo=gettz("UTC"))

        posts_count = len(self.site.all_posts)

        # find all published posts
        posts_published = [post for post in self.site.all_posts if post.use_in_feeds]
        posts_published = sorted(posts_published, key=lambda post: post.source_path)

        # find all private posts
        posts_private = [post for post in self.site.all_posts if post.is_private]
        posts_private = sorted(posts_private, key=lambda post: post.source_path)

        # find all drafts
        posts_drafts = [post for post in self.site.all_posts if post.is_draft]
        posts_drafts = sorted(posts_drafts, key=lambda post: post.source_path)

        # find all scheduled posts with offset from now until publishing time
        posts_scheduled = [
            (post.date - now, post) for post in self.site.all_posts
            if post.publish_later and not (post.is_draft or post.is_private)
        ]
        posts_scheduled = sorted(posts_scheduled, key=lambda offset_post: (offset_post[0], offset_post[1].source_path))

        if len(posts_scheduled) > 0:
            if options['list_scheduled']:
                for offset, post in posts_scheduled:
                    print("Scheduled: '{1}' ({2}; source: {3}) in {0}".format(self.human_time(offset), post.meta('title'), post.permalink(), post.source_path))
            else:
                offset, post = posts_scheduled[0]
                print("{0} to next scheduled post ('{1}'; {2}; source: {3}).".format(self.human_time(offset), post.meta('title'), post.permalink(), post.source_path))
        if options['list_drafts']:
            for post in posts_drafts:
                print("Draft: '{0}' ({1}; source: {2})".format(post.meta('title'), post.permalink(), post.source_path))
        if options['list_private']:
            for post in posts_private:
                print("Private: '{0}' ({1}; source: {2})".format(post.meta('title'), post.permalink(), post.source_path))
        if options['list_published']:
            for post in posts_published:
                print("Published: '{0}' ({1}; source: {2})".format(post.meta('title'), post.permalink(), post.source_path))
        print(f"{posts_count} posts in total, {len(posts_scheduled)} scheduled, {len(posts_drafts)} drafts, {len(posts_private)} private and {len(posts_published)} published.")

    def human_time(self, dt):
        """Translate time into a human-friendly representation."""
        days = dt.days
        hours = dt.seconds / 60 // 60
        minutes = dt.seconds / 60 - (hours * 60)
        if days > 0:
            return f"{days:.0f} days and {hours:.0f} hours"
        elif hours > 0:
            return f"{hours:.0f} hours and {minutes:.0f} minutes"
        elif minutes:
            return f"{minutes:.0f} minutes"
        return False
