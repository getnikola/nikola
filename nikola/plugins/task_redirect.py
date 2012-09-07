import os

from nikola.plugin_categories import Task
from nikola import utils


class Redirect(Task):
    """Copy theme assets into output."""

    name = "redirect"

    def gen_tasks(self):
        """Generate redirections tasks."""

        kw = {
            'redirections': self.site.config['REDIRECTIONS'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
        }

        if not kw['redirections']:
            # If there are no redirections, still needs to create a
            # dummy action so dependencies don't fail
            yield {
                'basename': self.name,
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }

        else:
            for src, dst in kw["redirections"]:
                src_path = os.path.join(kw["output_folder"], src)
                yield {
                    'basename': self.name,
                    'name': src_path,
                    'targets': [src_path],
                    'actions': [(create_redirect, (src_path, dst))],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                    }

def create_redirect(src, dst):
    with codecs.open(src, "wb+", "utf8") as fd:
        fd.write(('<head>' +
        '<meta HTTP-EQUIV="REFRESH" content="0; url=%s">' +
        '</head>') % dst)
