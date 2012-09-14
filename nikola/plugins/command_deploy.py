from optparse import OptionParser
import os

from nikola.plugin_categories import Command


class Deploy(Command):
    """Deploy site.  """
    name = "deploy"

    def run(self, *args):
        parser = OptionParser(usage="nikola %s [options]" % self.name)
        (options, args) = parser.parse_args(list(args))
        for command in self.site.config['DEPLOY_COMMANDS']:
            print "==>", command
            os.system(command)
