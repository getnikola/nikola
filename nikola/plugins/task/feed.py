# -*- coding: utf-8 -*-

# Copyright © 2015 IGARASHI Masanao

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

"""Generate RSS/Atom feeds."""

from __future__ import unicode_literals, print_function
import os
from nikola import utils
from nikola.plugin_categories import Task


class GenerateFeed(Task):
    """Generate RSS/Atom feeds."""

    name = "generate_feed"

    def set_site(self, site):
        """Set Nikola site."""
        site.register_path_handler('rss', self.rss_path)
        site.register_path_handler('atom', self.atom_path)
        return super(GenerateFeed, self).set_site(site)

    def gen_tasks(self):
        """Generate RSS/ATOM feeds."""
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "filters": self.site.config["FILTERS"],
            "blog_title": self.site.config["BLOG_TITLE"],
            "blog_author": self.site.config["BLOG_AUTHOR"],
            "site_url": self.site.config["SITE_URL"],
            "base_url": self.site.config["BASE_URL"],
            "blog_description": self.site.config["BLOG_DESCRIPTION"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "generate_atom": self.site.config["GENERATE_ATOM"],
            "generate_rss": self.site.config["GENERATE_RSS"],
            "feed_teasers": self.site.config["FEED_TEASERS"],
            "feed_plain": self.site.config["FEED_PLAIN"],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "feed_length": self.site.config['FEED_LENGTH'],
            "tzinfo": self.site.tzinfo,
            "feed_read_more_link": self.site.config["FEED_READ_MORE_LINK"],
            "feed_links_append_query": self.site.config["FEED_LINKS_APPEND_QUERY"],
            "feed_enclosure": self.site.config["FEED_ENCLOSURE"],
            "feed_previewimage_default": self.site.config["FEED_PREVIEWIMAGE_DEFAULT"],
            "feed_push": self.site.config["FEED_PUSH"],
            "feed_path": self.site.config["FEED_PATH"],
        }

        self.site.scan_posts()
        # Check for any changes in the state of use_in_feeds for any post.
        # Issue #934
        kw['use_in_feeds_status'] = ''.join(
            ['T' if x.use_in_feeds else 'F' for x in self.site.timeline]
        )
        yield self.group_task()

        if not kw['generate_atom'] and not kw['generate_rss']:
            return

        for lang in kw["translations"]:
            targets = []
            atom_path = self.site.link("atom", None, lang)
            if kw['generate_atom']:
                atom_output_name = os.path.join(kw['output_folder'],
                                                atom_path.lstrip('/'))
                targets.append(atom_output_name)
            else:
                atom_output_name = None
            if kw['generate_rss']:
                rss_path = self.site.link("rss", None, lang)
                rss_output_name = os.path.join(kw['output_folder'],
                                               rss_path.lstrip('/'))
                targets.append(rss_output_name)
            else:
                rss_path = None
                rss_output_name = None

            deps = []
            deps_uptodate = []
            if kw["show_untranslated_posts"]:
                posts = self.site.posts[:kw['feed_length']]
            else:
                posts = [x for x in self.site.posts
                         if x.is_translation_available(lang)][:kw['feed_length']]
            for post in posts:
                deps += post.deps(lang)
                deps_uptodate += post.deps_uptodate(lang)

            task = {
                'basename': GenerateFeed.name,
                'name': lang + ':' + ':'.join(targets),
                'actions': [(self.site.feedutil.gen_feed_generator,
                             (lang, posts, kw['base_url'],
                              kw['blog_title'](lang),
                              kw['blog_description'](lang),
                              atom_output_name, atom_path,
                              rss_output_name, rss_path))],
                'targets': targets,
                'file_dep': deps,
                'task_dep': ['render_posts'],
                'clean': True,
                'uptodate': [utils.config_changed(kw,'nikola.plugins.task.feed')] + deps_uptodate,
            }
            yield task

    def rss_path(self, name, lang):
        """A link to the RSS feed path.

        Example:

        link://rss => /blog/rss.xml
        """
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['FEED_PATH'], 'rss.xml'] if _f]

    def atom_path(self, name, lang):
        """A link to the Atom feed path.

        Example:

        link://atom => /blog/feed.atom
        """
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['FEED_PATH'], 'feed.atom'] if _f]
