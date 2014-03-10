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

from __future__ import unicode_literals

import codecs
import glob
import os
import sys
import subprocess

from nikola.plugin_categories import Task
from nikola import utils


class BuildLess(Task):
    """Generate CSS out of LESS sources."""

    name = "build_less"
    sources_folder = "less"
    sources_ext = ".less"

    def gen_tasks(self):
        """Generate CSS out of LESS sources."""
        self.compiler_name = self.site.config['LESS_COMPILER']
        self.compiler_options = self.site.config['LESS_OPTIONS']

        kw = {
            'cache_folder': self.site.config['CACHE_FOLDER'],
            'themes': self.site.THEMES,
        }
        tasks = {}

        # Find where in the theme chain we define the LESS targets
        # There can be many *.less in the folder, but we only will build
        # the ones listed in less/targets
        if os.path.isfile(os.path.join(self.sources_folder, "targets")):
            targets_path = os.path.join(self.sources_folder, "targets")
        else:
            targets_path = utils.get_asset_path(os.path.join(self.sources_folder, "targets"), self.site.THEMES)
        try:
            with codecs.open(targets_path, "rb", "utf-8") as inf:
                targets = [x.strip() for x in inf.readlines()]
        except Exception:
            targets = []

        for task in utils.copy_tree(self.sources_folder, os.path.join(kw['cache_folder'], self.sources_folder)):
            if task['name'] in tasks:
                continue
            task['basename'] = 'prepare_less_sources'
            tasks[task['name']] = task
            yield task

        for theme_name in kw['themes']:
            src = os.path.join(utils.get_theme_path(theme_name), self.sources_folder)
            for task in utils.copy_tree(src, os.path.join(kw['cache_folder'], self.sources_folder)):
                task['basename'] = 'prepare_less_sources'
                yield task

        # Build targets and write CSS files
        base_path = utils.get_theme_path(self.site.THEMES[0])
        dst_dir = os.path.join(self.site.config['OUTPUT_FOLDER'], 'assets', 'css')
        # Make everything depend on all sources, rough but enough
        deps = glob.glob(os.path.join(
            base_path,
            self.sources_folder,
            "*{0}".format(self.sources_ext)))

        def compile_target(target, dst):
            utils.makedirs(dst_dir)
            src = os.path.join(kw['cache_folder'], self.sources_folder, target)
            run_in_shell = sys.platform == 'win32'
            try:
                compiled = subprocess.check_output([self.compiler_name] + self.compiler_options + [src], shell=run_in_shell)
            except OSError:
                utils.req_missing([self.compiler_name],
                                  'build LESS files (and use this theme)',
                                  False, False)
            with open(dst, "wb+") as outf:
                outf.write(compiled)

        yield self.group_task()

        for target in targets:
            dst = os.path.join(dst_dir, target.replace(self.sources_ext, ".css"))
            yield {
                'basename': self.name,
                'name': dst,
                'targets': [dst],
                'file_dep': deps,
                'task_dep': ['prepare_less_sources'],
                'actions': ((compile_target, [target, dst]), ),
                'uptodate': [utils.config_changed(kw)],
                'clean': True
            }
