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

import os

from nikola.plugin_categories import Task
from nikola.utils import config_changed


class Archive(Task):
    """Render the post archives."""

    name = "render_archive"

    def gen_tasks(self):
        kw = {
            "messages": self.site.MESSAGES,
            "translations": self.site.config['TRANSLATIONS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
        }
        self.site.scan_posts()
        # TODO add next/prev links for years
        template_name = "list_post.tmpl"
        # TODO: posts_per_year is global, kill it
        for year, posts in list(self.site.posts_per_year.items()):
            for lang in kw["translations"]:
                output_name = os.path.join(
                    kw['output_folder'], self.site.path("archive", year,
                                                        lang))
                post_list = [self.site.global_data[post] for post in posts]
                post_list.sort(key=lambda a: a.date)
                post_list.reverse()
                context = {}
                context["lang"] = lang
                context["posts"] = post_list
                context["permalink"] = self.site.link("archive", year, lang)
                context["title"] = kw["messages"][lang]["Posts for year %s"]\
                    % year
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
                task['basename'] = self.name
                yield task

        # And global "all your years" page
        years = list(self.site.posts_per_year.keys())
        years.sort(reverse=True)
        template_name = "list.tmpl"
        kw['years'] = years
        for lang in kw["translations"]:
            context = {}
            output_name = os.path.join(
                kw['output_folder'], self.site.path("archive", None,
                                                    lang))
            context["title"] = kw["messages"][lang]["Archive"]
            context["items"] = [(year, self.site.link("archive", year, lang))
                                for year in years]
            context["permalink"] = self.site.link("archive", None, lang)
            task = self.site.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            )
            task_cfg = {1: task['uptodate'][0].config, 2: kw}
            task['uptodate'] = [config_changed(task_cfg)]
            task['basename'] = self.name
            yield task
