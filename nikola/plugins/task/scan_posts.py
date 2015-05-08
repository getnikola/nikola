# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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

from __future__ import unicode_literals, print_function
from collections import defaultdict
import glob
import os
import sys

from blinker import signal

from nikola.plugin_categories import Task
from nikola import utils
from nikola.post import Post


class ScanPosts(Task):
    """Render pages into output."""

    name = "scan_posts"

    def gen_tasks(self):
        """Build final pages from metadata and HTML fragments."""
        kw = {
            "post_pages": self.site.config["post_pages"],
            "translations": self.site.config["TRANSLATIONS"],
            "filters": self.site.config["FILTERS"],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "demote_headers": self.site.config['DEMOTE_HEADERS'],
        }
        self.site.global_data = {}
        self.site.posts = []
        self.site.all_posts = []
        self.site.posts_per_year = defaultdict(list)
        self.site.posts_per_month = defaultdict(list)
        self.site.posts_per_tag = defaultdict(list)
        self.site.posts_per_category = defaultdict(list)
        self.site.post_per_file = {}
        self.site.timeline = []
        self.site.pages = []

        seen = set([])
        if not self.site.quiet:
            print("Scanning posts", end='', file=sys.stderr)

        slugged_tags = set([])
        quit = False
        for wildcard, destination, template_name, use_in_feeds in \
                self.site.config['post_pages']:
            if not self.site.quiet:
                print(".", end='', file=sys.stderr)
            dirname = os.path.dirname(wildcard)
            for dirpath, _, _ in os.walk(dirname, followlinks=True):
                dest_dir = os.path.normpath(os.path.join(destination,
                                            os.path.relpath(dirpath, dirname)))  # output/destination/foo/
                # Get all the untranslated paths
                dir_glob = os.path.join(dirpath, os.path.basename(wildcard))  # posts/foo/*.rst
                untranslated = glob.glob(dir_glob)
                # And now get all the translated paths
                translated = set([])
                for lang in self.site.config['TRANSLATIONS'].keys():
                    if lang == self.site.config['DEFAULT_LANG']:
                        continue
                    lang_glob = utils.get_translation_candidate(self.site.config, dir_glob, lang)  # posts/foo/*.LANG.rst
                    translated = translated.union(set(glob.glob(lang_glob)))
                # untranslated globs like *.rst often match translated paths too, so remove them
                # and ensure x.rst is not in the translated set
                untranslated = set(untranslated) - translated

                # also remove from translated paths that are translations of
                # paths in untranslated_list, so x.es.rst is not in the untranslated set
                for p in untranslated:
                    translated = translated - set([utils.get_translation_candidate(self.site.config, p, l) for l in self.site.config['TRANSLATIONS'].keys()])

                full_list = list(translated) + list(untranslated)
                # We eliminate from the list the files inside any .ipynb folder
                full_list = [p for p in full_list
                             if not any([x.startswith('.')
                                         for x in p.split(os.sep)])]

                for base_path in full_list:
                    if base_path in seen:
                        continue
                    else:
                        seen.add(base_path)
                    post = Post(
                        base_path,
                        self.site.config,
                        dest_dir,
                        use_in_feeds,
                        self.site.MESSAGES,
                        template_name,
                        self.site.get_compiler(base_path)
                    )
                    self.site.timeline.append(post)
                    self.site.global_data[post.source_path] = post
                    if post.use_in_feeds:
                        self.site.posts.append(post)
                        self.site.posts_per_year[
                            str(post.date.year)].append(post)
                        self.site.posts_per_month[
                            '{0}/{1:02d}'.format(post.date.year, post.date.month)].append(post)
                        for tag in post.alltags:
                            _tag_slugified = utils.slugify(tag)
                            if _tag_slugified in slugged_tags:
                                if tag not in self.site.posts_per_tag:
                                    # Tags that differ only in case
                                    other_tag = [existing for existing in self.site.posts_per_tag.keys() if utils.slugify(existing) == _tag_slugified][0]
                                    utils.LOGGER.error('You have tags that are too similar: {0} and {1}'.format(tag, other_tag))
                                    utils.LOGGER.error('Tag {0} is used in: {1}'.format(tag, post.source_path))
                                    utils.LOGGER.error('Tag {0} is used in: {1}'.format(other_tag, ', '.join([p.source_path for p in self.site.posts_per_tag[other_tag]])))
                                    quit = True
                            else:
                                slugged_tags.add(utils.slugify(tag, force=True))
                            self.site.posts_per_tag[tag].append(post)
                        self.site.posts_per_category[post.meta('category')].append(post)

                    if post.is_post:
                        # unpublished posts
                        self.site.all_posts.append(post)
                    else:
                        self.site.pages.append(post)

                    for lang in self.site.config['TRANSLATIONS'].keys():
                        self.site.post_per_file[post.destination_path(lang=lang)] = post
                        self.site.post_per_file[post.destination_path(lang=lang, extension=post.source_ext())] = post

        # Sort everything.
        self.site.timeline.sort(key=lambda p: p.date)
        self.site.timeline.reverse()
        self.site.posts.sort(key=lambda p: p.date)
        self.site.posts.reverse()
        self.site.all_posts.sort(key=lambda p: p.date)
        self.site.all_posts.reverse()
        self.site.pages.sort(key=lambda p: p.date)
        self.site.pages.reverse()

        for i, p in enumerate(self.site.posts[1:]):
            p.next_post = self.site.posts[i]
        for i, p in enumerate(self.site.posts[:-1]):
            p.prev_post = self.site.posts[i + 1]
        self.site._scanned = True
        if not self.site.quiet:
            print("done!", file=sys.stderr)

        signal('scanned').send(self)

        if quit and not ignore_quit:
            sys.exit(1)

        yield self.group_task()
