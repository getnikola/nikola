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

"""Copy page sources into the output."""

import os

from nikola.plugin_categories import Task
from nikola import utils


class Sources(Task):
    """Copy page sources into the output."""

    name = "render_sources"

    def gen_tasks(self):
        """Publish the page sources into the output."""
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "default_lang": self.site.config["DEFAULT_LANG"],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
        }

        self.site.scan_posts()
        yield self.group_task()
        if self.site.config['COPY_SOURCES']:
            for lang in kw["translations"]:
                for post in self.site.timeline:
                    if not kw["show_untranslated_posts"] and lang not in post.translated_to:
                        continue
                    if post.meta('password'):
                        continue
                    output_name = os.path.join(
                        kw['output_folder'], post.destination_path(
                            lang, post.source_ext(True)))
                    # do not publish PHP sources
                    if post.source_ext(True) == post.compiler.extension():
                        continue
                    source = post.source_path
                    if lang != kw["default_lang"]:
                        source_lang = utils.get_translation_candidate(self.site.config, source, lang)
                        if os.path.exists(source_lang):
                            source = source_lang
                    if os.path.isfile(source):
                        yield {
                            'basename': 'render_sources',
                            'name': os.path.normpath(output_name),
                            'file_dep': [source],
                            'targets': [output_name],
                            'actions': [(utils.copy_file, (source, output_name))],
                            'clean': True,
                            'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.sources')],
                        }
