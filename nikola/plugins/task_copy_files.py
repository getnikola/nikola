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

        flag = False
        for src in kw['files_folders']:
            dst = kw['output_folder']
            filters = kw['filters']
            real_dst = os.path.join(dst, kw['files_folders'][src])
            for task in utils.copy_tree(src, real_dst, link_cutoff=dst):
                flag = True
                task['basename'] = self.name
                task['uptodate'] = task.get('uptodate', []) +\
                    [utils.config_changed(kw)]
                yield utils.apply_filters(task, filters)
        if not flag:
            yield {
                'basename': self.name,
                'actions': (),
            }

