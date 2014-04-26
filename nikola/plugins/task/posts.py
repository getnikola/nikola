# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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

from copy import copy

from nikola.plugin_categories import Task
from nikola import utils


def rest_deps(post, task):
    """Add extra_deps from ReST into task.

    The .dep file is created by ReST so not available before the task starts
    to execute.
    """
    task.file_dep.update(post.extra_deps())


class RenderPosts(Task):
    """Build HTML fragments from metadata and text."""

    name = "render_posts"

    def gen_tasks(self):
        """Build HTML fragments from metadata and text."""
        self.site.scan_posts()
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "timeline": self.site.timeline,
            "default_lang": self.site.config["DEFAULT_LANG"],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "demote_headers": self.site.config['DEMOTE_HEADERS'],
        }

        yield self.group_task()

        for lang in kw["translations"]:
            deps_dict = copy(kw)
            deps_dict.pop('timeline')
            for post in kw['timeline']:
                dest = post.translated_base_path(lang)
                task = {
                    'basename': self.name,
                    'name': dest,
                    'file_dep': post.fragment_deps(lang),
                    'targets': [dest],
                    'actions': [(post.compile, (lang, )),
                                (rest_deps, (post,)),
                                ],
                    'clean': True,
                    'uptodate': [utils.config_changed(deps_dict)],
                }
                yield task
