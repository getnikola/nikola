# Copyright (c) 2012 Roberto Alsina y otros.

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
import glob
import os

from nikola.plugin_categories import Task
from nikola.utils import config_changed


class Indexes(Task):
    """Render the blog indexes."""

    name = "render_indexes"

    def gen_tasks(self):
        self.site.scan_posts()

        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "index_display_post_count":
            self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "messages": self.site.MESSAGES,
            "index_teasers": self.site.config['INDEX_TEASERS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "hide_untranslated_posts": self.site.config['HIDE_UNTRANSLATED_POSTS'],
            "indexes_title": self.site.config['INDEXES_TITLE'],
            "indexes_pages": self.site.config['INDEXES_PAGES'],
            "blog_title": self.site.config["BLOG_TITLE"],
        }

        template_name = "index.tmpl"
        posts = [x for x in self.site.timeline if x.use_in_feeds]
        for lang in kw["translations"]:
            # Split in smaller lists
            lists = []
            if kw["hide_untranslated_posts"]:
                filtered_posts = [x for x in posts if x.is_translation_available(lang)]
            else:
                filtered_posts = posts
            lists.append(filtered_posts[:kw["index_display_post_count"]])
            while filtered_posts:
                lists.append(filtered_posts[-kw["index_display_post_count"]:])
                filtered_posts = filtered_posts[:-kw["index_display_post_count"]]
            num_pages = len(lists)
            for i, post_list in enumerate(lists):
                context = {}
                indexes_title = kw['indexes_title'] or kw['blog_title']
                if kw["indexes_pages"]:
                    indexes_pages = kw["indexes_pages"] % i
                else:
                    indexes_pages = " (" + \
                        kw["messages"][lang]["old posts page %d"] % i + ")"
                context["title"] = indexes_title + indexes_pages
                context["prevlink"] = None
                context["nextlink"] = None
                context['index_teasers'] = kw['index_teasers']
                if i == 0:  # index.html page
                    context["prevlink"] = None
                    if num_pages > 2:
                        context["nextlink"] = "index-{0}.html".format(num_pages - 2)
                    else:
                        context["nextlink"] = None
                else:  # index-x.html pages
                    if i > 1:
                        context["nextlink"] = "index-{0}.html".format(i - 1)
                    if i < num_pages - 1:
                        context["prevlink"] = "index-{0}.html".format(i + 1)
                context["permalink"] = self.site.link("index", i, lang)
                output_name = os.path.join(
                    kw['output_folder'], self.site.path("index", i,
                                                        lang))
                task = self.site.generic_post_list_renderer(
                    lang,
                    post_list,
                    output_name,
                    template_name,
                    kw['filters'],
                    context,
                )
                task_cfg = {1: task['uptodate'][0].config, 2: kw}
                task['uptodate'] = [config_changed(task_cfg)]
                task['basename'] = 'render_indexes'
                yield task

        if not self.site.config["STORY_INDEX"]:
            return
        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "post_pages": self.site.config["post_pages"],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
        }
        template_name = "list.tmpl"
        for lang in kw["translations"]:
            for wildcard, dest, _, is_post in kw["post_pages"]:
                if is_post:
                    continue
                context = {}
                # vim/pyflakes thinks it's unused
                # src_dir = os.path.dirname(wildcard)
                files = glob.glob(wildcard)
                post_list = [self.site.global_data[os.path.splitext(p)[0]] for
                             p in files]
                output_name = os.path.join(kw["output_folder"],
                                           self.site.path("post_path",
                                                          wildcard,
                                                          lang)).encode('utf8')
                context["items"] = [(post.title(lang), post.permalink(lang))
                                    for post in post_list]
                task = self.site.generic_post_list_renderer(lang, post_list,
                                                            output_name,
                                                            template_name,
                                                            kw['filters'],
                                                            context)
                task_cfg = {1: task['uptodate'][0].config, 2: kw}
                task['uptodate'] = [config_changed(task_cfg)]
                task['basename'] = self.name
                yield task
