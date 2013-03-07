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

from copy import copy
import os

from nikola.plugin_categories import Task
from nikola import utils


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
        }

        flag = False
        for lang in kw["translations"]:
            # TODO: timeline is global, get rid of it
            deps_dict = copy(kw)
            deps_dict.pop('timeline')
            for post in kw['timeline']:
                source = post.source_path
                dest = post.base_path
                if lang != kw["default_lang"]:
                    dest += '.' + lang
                    source_lang = source + '.' + lang
                    if os.path.exists(source_lang):
                        source = source_lang
                    elif self.site.config['HIDE_UNTRANSLATED_POSTS']:
                        continue
                flag = True
                yield {
                    'basename': self.name,
                    'name': dest.encode('utf-8'),
                    'file_dep': post.fragment_deps(lang),
                    'targets': [dest],
                    'actions': [(self.site.get_compiler(post.source_path),
                                 [source, dest])],
                    'clean': True,
                    'uptodate': [utils.config_changed(deps_dict)],
                }
        if flag is False:  # Return a dummy task
            yield {
                'basename': self.name,
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }
