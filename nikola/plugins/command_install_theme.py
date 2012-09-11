from optparse import OptionParser
import os
import urllib2
import json
from StringIO import StringIO

from nikola.plugin_categories import Command
from nikola import utils


class CommandInstallTheme(Command):
    """Start test server."""

    name = "install_theme"

    def run(self, *args):
        """Install theme into current site."""

        parser = OptionParser()
        parser.add_option("-l", "--list", dest="list",
            action="store_true",
            help="Show list of available themes.")
        parser.add_option("-n", "--name", dest="name",
            help="Theme name", default=None)
        parser.add_option("-u", "--url", dest="url",
            help="URL for the theme repository"
            "(default: http://nikola.ralsina.com.ar/themes/index.json)",
            default='http://nikola.ralsina.com.ar/themes/index.json')
        (options, args) = parser.parse_args(list(args))

        listing = options.list
        name = options.name
        url = options.url

        if name is None and not listing:
            print "This command needs either the -n or the -l option."
            return False
        data = urllib2.urlopen(url).read()
        data = json.loads(data)
        if listing:
            print "Themes:"
            print "-------"
            for theme in sorted(data.keys()):
                print theme
            return True
        else:
            if name in data:
                if os.path.isfile("themes"):
                    raise IOError("'themes' isn't a directory!")
                elif not os.path.isdir("themes"):
                    try:
                        os.makedirs("themes")
                    except:
                        raise OSError("mkdir 'theme' error!")
                print 'Downloading: %s' % data[name]
                zip_file = StringIO()
                zip_file.write(urllib2.urlopen(data[name]).read())
                print 'Extracting: %s into themes' % name
                utils.extract_all(zip_file)
            else:
                print "Can't find theme %s" % name
                return False
