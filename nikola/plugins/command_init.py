from optparse import OptionParser
import os
import shutil

import nikola
from nikola.plugin_categories import Command


class CommandInit(Command):
    """Create a new site."""

    name = "init"

    usage = """Usage: nikola init folder [options].

That will create a sample site in the specified folder.
The destination folder must not exist.
"""

    def run(self, *args):
        """Create a new site."""
        parser = OptionParser(usage=self.usage)
        (options, args) = parser.parse_args(list(args))

        target = args[0]
        if target is None:
            print self.usage
        else:
            src = os.path.join(os.path.dirname(nikola.__file__),
                'data', 'samplesite')
            shutil.copytree(src, target)
            print "A new site with some sample data has been created at %s."\
                % target
            print "See README.txt in that folder for more information."
