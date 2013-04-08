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
from nikola.plugin_categories import Task
from nikola.utils import config_changed


class RenderPages(Task):
    """Render pages into output."""

    name = "render_pages"

    def gen_tasks(self):
        """Build final pages from metadata and HTML fragments."""
        kw = {
            "post_pages": self.site.config["post_pages"],
            "translations": self.site.config["TRANSLATIONS"],
            "filters": self.site.config["FILTERS"],
            "hide_untranslated_posts": self.site.config['HIDE_UNTRANSLATED_POSTS'],
        }
        self.site.scan_posts()
        flag = False
        for lang in kw["translations"]:
            for post in self.site.timeline:
                if kw["hide_untranslated_posts"] and not post.is_translation_available(lang):
                    continue
                for task in self.site.generic_page_renderer(lang, post,
                                                            kw["filters"]):
                    task['uptodate'] = [config_changed({
                        1: task['uptodate'][0].config,
                        2: kw})]
                    task['basename'] = self.name
                    task['task_dep'] = ['render_posts']
                    flag = True
                    yield task
        if flag is False:  # No page rendered, yield a dummy task
            yield {
                'basename': self.name,
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }
