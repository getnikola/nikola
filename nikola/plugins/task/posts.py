# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

"""Build HTML fragments from metadata and text."""

import docutils
import os
from copy import copy

from nikola.plugin_categories import Task
from nikola import utils


def update_deps(post, lang, task):
    """Update file dependencies as they might have been updated during compilation.

    This is done for example by the ReST page compiler, which writes its
    dependencies into a .dep file. This file is read and incorporated when calling
    post.fragment_deps(), and only available /after/ compiling the fragment.
    """
    task.file_dep.update([p for p in post.fragment_deps(lang) if not p.startswith("####MAGIC####")])


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
            "docutils_version": docutils.__version__,
        }
        self.tl_changed = False

        yield self.group_task()

        def tl_ch():
            self.tl_changed = True

        yield {
            'basename': self.name,
            'name': 'timeline_changes',
            'actions': [tl_ch],
            'uptodate': [utils.config_changed({1: kw['timeline']})],
        }

        for lang in kw["translations"]:
            deps_dict = copy(kw)
            deps_dict.pop('timeline')
            for post in kw['timeline']:
                if not post.is_translation_available(lang) and not self.site.config['SHOW_UNTRANSLATED_POSTS']:
                    continue
                # Extra config dependencies picked from config
                for p in post.fragment_deps(lang):
                    if p.startswith('####MAGIC####CONFIG:'):
                        k = p.split('####MAGIC####CONFIG:', 1)[-1]
                        deps_dict[k] = self.site.config.get(k)
                dest = post.translated_base_path(lang)
                file_dep = [p for p in post.fragment_deps(lang) if not p.startswith("####MAGIC####")]
                extra_targets = post.compiler.get_extra_targets(post, lang, dest)
                task = {
                    'basename': self.name,
                    'name': dest,
                    'file_dep': file_dep,
                    'targets': [dest] + extra_targets,
                    'actions': [(post.compile, (lang, )),
                                (update_deps, (post, lang, )),
                                ],
                    'clean': True,
                    'uptodate': [
                        utils.config_changed(deps_dict, 'nikola.plugins.task.posts'),
                        lambda p=post, l=lang: self.dependence_on_timeline(p, l)
                    ] + post.fragment_deps_uptodate(lang),
                    'task_dep': ['render_posts:timeline_changes']
                }

                # Apply filters specified in the metadata
                ff = [x.strip() for x in post.meta('filters', lang).split(',')]
                flist = []
                for i, f in enumerate(ff):
                    if not f:
                        continue
                    _f = self.site.filters.get(f)
                    if _f is not None:  # A registered filter
                        flist.append(_f)
                    else:
                        flist.append(f)
                yield utils.apply_filters(task, {os.path.splitext(dest)[-1]: flist})

    def dependence_on_timeline(self, post, lang):
        """Check if a post depends on the timeline."""
        if "####MAGIC####TIMELINE" not in post.fragment_deps(lang):
            return True  # No dependency on timeline
        elif self.tl_changed:
            return False  # Timeline changed
        return True
