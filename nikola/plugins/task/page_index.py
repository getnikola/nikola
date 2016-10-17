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

from nikola.plugin_categories import Task
from nikola import utils


class PageIndex(Task):
    """Render the page index."""

    name = "render_page_index"

    def set_site(self, site):
        """Set Nikola site."""
        return super(PageIndex, self).set_site(site)

    def gen_tasks(self):
        """Render the blog indexes."""
        self.site.scan_posts()
        yield self.group_task()

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
