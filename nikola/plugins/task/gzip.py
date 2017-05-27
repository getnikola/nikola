# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Create gzipped copies of files."""

import gzip
import os
import shlex
import subprocess

from nikola.plugin_categories import TaskMultiplier


class GzipFiles(TaskMultiplier):
    """If appropiate, create tasks to create gzipped versions of files."""

    name = "gzip"
    is_default = True

    def process(self, task, prefix):
        """Process tasks."""
        if not self.site.config['GZIP_FILES']:
            return []
        if task.get('name') is None:
            return []
        gzip_task = {
            'file_dep': [],
            'targets': [],
            'actions': [],
            'basename': '{0}_gzip'.format(prefix),
            'name': task.get('name').split(":", 1)[-1] + '.gz',
            'clean': True,
        }
        targets = task.get('targets', [])
        flag = False
        for target in targets:
            ext = os.path.splitext(target)[1]
            if (ext.lower() in self.site.config['GZIP_EXTENSIONS'] and
                    target.startswith(self.site.config['OUTPUT_FOLDER'])):
                flag = True
                gzipped = target + '.gz'
                gzip_task['file_dep'].append(target)
                gzip_task['targets'].append(gzipped)
                gzip_task['actions'].append((create_gzipped_copy, (target, gzipped, self.site.config['GZIP_COMMAND'])))
        if not flag:
            return []
        return [gzip_task]


def create_gzipped_copy(in_path, out_path, command=None):
    """Create gzipped copy of in_path and save it as out_path."""
    if command:
        subprocess.check_call(shlex.split(command.format(filename=in_path)))
    else:
        with gzip.GzipFile(out_path, 'wb+') as outf:
            with open(in_path, 'rb') as inf:
                outf.write(inf.read())
