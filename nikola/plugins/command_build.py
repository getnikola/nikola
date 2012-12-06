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
            first = args[0] if args else None
            if first in ('auto', 'clean', 'forget', 'ignore', 'list', 'run'):
                cmd = first
                args = args[1:]
            else:
                cmd = 'run'
            os.system('doit %s -f %s -d . %s' % (cmd, dodo.name, ' '.join(args)))

