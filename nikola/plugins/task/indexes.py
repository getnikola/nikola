# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Render the blog indexes."""

from __future__ import unicode_literals
from collections import defaultdict
import os
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA

from nikola.plugin_categories import Task
from nikola import utils
from nikola.nikola import _enclosure


class Indexes(Task):
    """Render the blog indexes."""

    name = "render_indexes"

    def set_site(self, site):
        """Set Nikola site."""
        self.number_of_pages = dict()
        site.register_path_handler('index', self.index_path)
        site.register_path_handler('index_atom', self.index_atom_path)
        return super(Indexes, self).set_site(site)

    def _get_filtered_posts(self, lang, show_untranslated_posts):
        """Return a filtered list of all posts for the given language.

        If show_untranslated_posts is True, will only include posts which
        are translated to the given language. Otherwise, returns all posts.
        """
        if show_untranslated_posts:
            return self.site.posts
        else:
            return [x for x in self.site.posts if x.is_translation_available(lang)]

    def _compute_number_of_pages(self, filtered_posts, posts_count):
        """Given a list of posts and the maximal number of posts per page, computes the number of pages needed."""
        return min(1, (len(filtered_posts) + posts_count - 1) // posts_count)

    def gen_tasks(self):
        """Render the blog indexes."""
        self.site.scan_posts()
        yield self.group_task()

        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "messages": self.site.MESSAGES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "feed_length": self.site.config['FEED_LENGTH'],
            "feed_links_append_query": self.site.config["FEED_LINKS_APPEND_QUERY"],
            "feed_teasers": self.site.config["FEED_TEASERS"],
            "feed_plain": self.site.config["FEED_PLAIN"],
            "filters": self.site.config['FILTERS'],
            "index_file": self.site.config['INDEX_FILE'],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "index_display_post_count": self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "indexes_title": self.site.config['INDEXES_TITLE'],
            "strip_indexes": self.site.config['STRIP_INDEXES'],
            "blog_title": self.site.config["BLOG_TITLE"],
            "generate_atom": self.site.config["GENERATE_ATOM"],
            "site_url": self.site.config["SITE_URL"],
        }

        template_name = "index.tmpl"
        for lang in kw["translations"]:
            def page_link(i, displayed_i, num_pages, force_addition, extension=None):
                feed = "_atom" if extension == ".atom" else ""
                return utils.adjust_name_for_index_link(self.site.link("index" + feed, None, lang), i, displayed_i,
                                                        lang, self.site, force_addition, extension)

            def page_path(i, displayed_i, num_pages, force_addition, extension=None):
                feed = "_atom" if extension == ".atom" else ""
                return utils.adjust_name_for_index_path(self.site.path("index" + feed, None, lang), i, displayed_i,
                                                        lang, self.site, force_addition, extension)

            filtered_posts = self._get_filtered_posts(lang, kw["show_untranslated_posts"])

            indexes_title = kw['indexes_title'](lang) or kw['blog_title'](lang)
            self.number_of_pages[lang] = self._compute_number_of_pages(filtered_posts, kw['index_display_post_count'])

            context = {}
            context["pagekind"] = ["main_index", "index"]

            yield self.site.generic_index_renderer(lang, filtered_posts, indexes_title, template_name, context, kw, 'render_indexes', page_link, page_path)

        if not self.site.config["PAGE_INDEX"]:
            return
        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "post_pages": self.site.config["post_pages"],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "index_file": self.site.config['INDEX_FILE'],
            "strip_indexes": self.site.config['STRIP_INDEXES'],
        }
        template_name = "list.tmpl"
        index_len = len(kw['index_file'])
        for lang in kw["translations"]:
            # Need to group by folder to avoid duplicated tasks (Issue #758)
                # Group all pages by path prefix
                groups = defaultdict(list)
                for p in self.site.timeline:
                    if not p.is_post:
                        destpath = p.destination_path(lang)
                        if destpath[-(1 + index_len):] == '/' + kw['index_file']:
                            destpath = destpath[:-(1 + index_len)]
                        dirname = os.path.dirname(destpath)
                        groups[dirname].append(p)
                for dirname, post_list in groups.items():
                    context = {}
                    context["items"] = []
                    should_render = True
                    output_name = os.path.join(kw['output_folder'], dirname, kw['index_file'])
                    short_destination = os.path.join(dirname, kw['index_file'])
                    link = short_destination.replace('\\', '/')
                    if kw['strip_indexes'] and link[-(1 + index_len):] == '/' + kw['index_file']:
                        link = link[:-index_len]
                    context["permalink"] = link
                    context["pagekind"] = ["list"]
                    if dirname == "/":
                        context["pagekind"].append("front_page")

                    for post in post_list:
                        # If there is an index.html pending to be created from
                        # a page, do not generate the PAGE_INDEX
                        if post.destination_path(lang) == short_destination:
                            should_render = False
                        else:
                            context["items"].append((post.title(lang),
                                                     post.permalink(lang),
                                                     None))

                    if should_render:
                        task = self.site.generic_post_list_renderer(lang, post_list,
                                                                    output_name,
                                                                    template_name,
                                                                    kw['filters'],
                                                                    context)
                        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.indexes')]
                        task['basename'] = self.name
                        yield task

    def index_path(self, name, lang, is_feed=False):
        """Link to a numbered index.

        Example:

        link://index/3 => /index-3.html
        """
        extension = None
        if is_feed:
            extension = ".atom"
            index_file = os.path.splitext(self.site.config['INDEX_FILE'])[0] + extension
        else:
            index_file = self.site.config['INDEX_FILE']
        if lang in self.number_of_pages:
            number_of_pages = self.number_of_pages[lang]
        else:
            number_of_pages = self._compute_number_of_pages(self._get_filtered_posts(lang, self.site.config['SHOW_UNTRANSLATED_POSTS']), self.site.config['INDEX_DISPLAY_POST_COUNT'])
            self.number_of_pages[lang] = number_of_pages
        return utils.adjust_name_for_index_path_list([_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                                                    self.site.config['INDEX_PATH'],
                                                                    index_file] if _f],
                                                     name,
                                                     utils.get_displayed_page_number(name, number_of_pages, self.site),
                                                     lang,
                                                     self.site,
                                                     extension=extension)

    def index_atom_path(self, name, lang):
        """Link to a numbered Atom index.

        Example:

        link://index_atom/3 => /index-3.atom
        """
        return self.index_path(name, lang, is_feed=True)
