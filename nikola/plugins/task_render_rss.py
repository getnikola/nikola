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

from nikola import utils
from nikola.plugin_categories import Task


class RenderRSS(Task):
    """Generate RSS feeds."""

    name = "render_rss"

    def gen_tasks(self):
        """Generate RSS feeds."""
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "filters": self.site.config["FILTERS"],
            "blog_title": self.site.config["BLOG_TITLE"],
            "site_url": self.site.config["SITE_URL"],
            "blog_description": self.site.config["BLOG_DESCRIPTION"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "rss_teasers": self.site.config["RSS_TEASERS"],
            "hide_untranslated_posts": self.site.config['HIDE_UNTRANSLATED_POSTS'],
        }
        self.site.scan_posts()
        for lang in kw["translations"]:
            output_name = os.path.join(kw['output_folder'],
                                       self.site.path("rss", None, lang))
            deps = []
            if kw["hide_untranslated_posts"]:
                posts = [x for x in self.site.timeline if x.use_in_feeds
                         and x.is_translation_available(lang)][:10]
            else:
                posts = [x for x in self.site.timeline if x.use_in_feeds][:10]
            for post in posts:
                deps += post.deps(lang)
            yield {
                'basename': 'render_rss',
                'name': os.path.normpath(output_name),
                'file_dep': deps,
                'targets': [output_name],
                'actions': [(utils.generic_rss_renderer,
                            (lang, kw["blog_title"], kw["site_url"],
                             kw["blog_description"], posts, output_name,
                             kw["rss_teasers"]))],
                'task_dep': ['render_posts'],
                'clean': True,
                'uptodate': [utils.config_changed(kw)],
            }
