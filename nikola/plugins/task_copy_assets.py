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

import codecs
import os

from nikola.plugin_categories import Task
from nikola import utils


class CopyAssets(Task):
    """Copy theme assets into output."""

    name = "copy_assets"

    def gen_tasks(self):
        """Create tasks to copy the assets of the whole theme chain.

        If a file is present on two themes, use the version
        from the "youngest" theme.
        """

        kw = {
            "themes": self.site.THEMES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "code_color_scheme": self.site.config['CODE_COLOR_SCHEME'],
        }
        flag = True
        has_code_css = False
        tasks = {}
        code_css_path = os.path.join(kw['output_folder'], 'assets', 'css', 'code.css')
        for theme_name in kw['themes']:
            src = os.path.join(utils.get_theme_path(theme_name), 'assets')
            dst = os.path.join(kw['output_folder'], 'assets')
            for task in utils.copy_tree(src, dst):
                if task['name'] in tasks:
                    continue
                if task['targets'][0] == code_css_path:
                    has_code_css = True
                tasks[task['name']] = task
                task['uptodate'] = [utils.config_changed(kw)]
                task['basename'] = self.name
                flag = False
                yield utils.apply_filters(task, kw['filters'])

        if flag:
            yield {
                'basename': self.name,
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }

        if not has_code_css:  # Generate it

            def create_code_css():
                from pygments.formatters import get_formatter_by_name
                formatter = get_formatter_by_name('html', style=kw["code_color_scheme"])
                try:
                    os.makedirs(os.path.dirname(code_css_path))
                except:
                    pass
                with codecs.open(code_css_path, 'wb+', 'utf8') as outf:
                    outf.write(formatter.get_style_defs('.code'))
                    outf.write("table.codetable { width: 100%;} td.linenos {text-align: right; width: 4em;}")

            task = {
                'basename': self.name,
                'name': code_css_path,
                'targets': [code_css_path],
                'uptodate': [utils.config_changed(kw)],
                'actions': [(create_code_css, [])],
                'clean': True,
            }
            yield utils.apply_filters(task, kw['filters'])
