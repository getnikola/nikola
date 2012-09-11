import os
import tempfile

from nikola.plugin_categories import Command


class CommandBuild(Command):
    """Build the site."""

    name = "build"

    def run(self, *args):
        """Build the site using doit."""

        # FIXME: this is crap, do it right
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as dodo:
            dodo.write('''
from doit.reporter import ExecutedOnlyReporter
DOIT_CONFIG = {
        'reporter': ExecutedOnlyReporter,
        'default_tasks': ['render_site'],
}
from nikola import Nikola
import conf
SITE = Nikola(**conf.__dict__)


def task_render_site():
    return SITE.gen_tasks()
            ''')
            dodo.flush()
            os.system('doit -f %s -d . %s' % (dodo.name, ' '.join(args)))
