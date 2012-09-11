import os
import shutil

import nikola
from nikola.plugin_categories import Command


class CommandInit(Command):
    """Create a new site."""

    name = "init"

    usage = """To create a new site in a folder, run "nikola init foldername".

The destination folder must not exist.

If you pass the src argument, that folder will be used as a template for
the new site instead of Nikola's sample site.
"""

    def run(self, target=None):
        """Create a new site."""
        if target is None:
            print self.usage
        else:
            src = os.path.join(os.path.dirname(nikola.__file__),
                'data', 'samplesite')
            shutil.copytree(src, target)
            print "A new site with some sample data has been created at %s."\
                % target
            print "See README.txt in that folder for more information."
