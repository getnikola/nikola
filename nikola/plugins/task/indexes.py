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

from __future__ import unicode_literals
from collections import defaultdict
import os

from nikola.plugin_categories import Task
from nikola import utils


class Indexes(Task):
    """Render the blog indexes."""

    name = "render_indexes"

    def set_site(self, site):
        site.register_path_handler('index', self.index_path)
        site.register_path_handler('index_atom', self.index_atom_path)
        return super(Indexes, self).set_site(site)

    def gen_tasks(self):
        self.site.scan_posts()
        yield self.group_task()

        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "messages": self.site.MESSAGES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "index_display_post_count": self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "indexes_title": self.site.config['INDEXES_TITLE'],
            "blog_title": self.site.config["BLOG_TITLE"],
            "generate_atom": self.site.config["GENERATE_ATOM"],
        }

        template_name = "index.tmpl"
        posts = self.site.posts
        self.number_of_pages = dict()
        for lang in kw["translations"]:
            def page_link(i, displayed_i, num_pages, force_addition, extension=None):
                feed = "_atom" if extension == ".atom" else ""
                return utils.adjust_name_for_index_link(self.site.link("index" + feed, None, lang), i, displayed_i,
                                                        lang, self.site, force_addition, extension)

            def page_path(i, displayed_i, num_pages, force_addition, extension=None):
                feed = "_atom" if extension == ".atom" else ""
                return utils.adjust_name_for_index_path(self.site.path("index" + feed, None, lang), i, displayed_i,
                                                        lang, self.site, force_addition, extension)

            if kw["show_untranslated_posts"]:
                filtered_posts = posts
            else:
                filtered_posts = [x for x in posts if x.is_translation_available(lang)]

            indexes_title = kw['indexes_title'](lang) or kw['blog_title'](lang)
            self.number_of_pages[lang] = (len(filtered_posts) + kw['index_display_post_count'] - 1) // kw['index_display_post_count']

            yield self.site.generic_index_renderer(lang, filtered_posts, indexes_title, template_name, {}, kw, 'render_indexes', page_link, page_path)

        if not self.site.config["STORY_INDEX"]:
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
        for lang in kw["translations"]:
            # Need to group by folder to avoid duplicated tasks (Issue #758)
                # Group all pages by path prefix
                groups = defaultdict(list)
                for p in self.site.timeline:
                    if not p.is_post:
                        dirname = os.path.dirname(p.destination_path(lang))
                        groups[dirname].append(p)
                for dirname, post_list in groups.items():
                    context = {}
                    context["items"] = []
                    should_render = True
                    output_name = os.path.join(kw['output_folder'], dirname, kw['index_file'])
                    short_destination = os.path.join(dirname, kw['index_file'])
                    link = short_destination.replace('\\', '/')
                    index_len = len(kw['index_file'])
                    if kw['strip_indexes'] and link[-(1 + index_len):] == '/' + kw['index_file']:
                        link = link[:-index_len]
                    context["permalink"] = link

                    for post in post_list:
                        # If there is an index.html pending to be created from
                        # a story, do not generate the STORY_INDEX
                        if post.destination_path(lang) == short_destination:
                            should_render = False
                        else:
                            context["items"].append((post.title(lang),
                                                     post.permalink(lang)))

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
        extension = None
        if is_feed:
            extension = ".atom"
            index_file = os.path.splitext(self.site.config['INDEX_FILE'])[0] + extension
        else:
            index_file = self.site.config['INDEX_FILE']
        return utils.adjust_name_for_index_path_list([_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                                                    self.site.config['INDEX_PATH'],
                                                                    index_file] if _f],
                                                     name,
                                                     utils.get_displayed_page_number(name, self.number_of_pages[lang], self.site),
                                                     lang,
                                                     self.site,
                                                     extension=extension)

    def index_atom_path(self, name, lang):
        return self.index_path(name, lang, is_feed=True)
