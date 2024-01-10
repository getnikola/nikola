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

"""Copy static files into the output folder."""

import os

from nikola.plugin_categories import Task
from nikola import utils


class CopyFiles(Task):
    """Copy static files into the output folder."""

    name = "copy_files"

    def gen_tasks(self):
        """Copy static files into the output folder."""
        kw = {
            'files_folders': self.site.config['FILES_FOLDERS'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'filters': self.site.config['FILTERS'],
        }

        yield self.group_task()
        for src in kw['files_folders']:
            dst = kw['output_folder']
            filters = kw['filters']
            real_dst = os.path.join(dst, kw['files_folders'][src])
            for task in utils.copy_tree(src, real_dst, link_cutoff=dst):
                task['basename'] = self.name
                task['uptodate'] = [utils.config_changed(kw, 'nikola.plugins.task.copy_files')]
                yield utils.apply_filters(task, filters, skip_ext=['.html'])
