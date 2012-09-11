from optparse import OptionParser
import os
import urllib2

from nikola.plugin_categories import Command


class CommandBootswatchTheme(Command):
    """Given a swatch name and a parent theme, creates a custom theme."""

    name = "bootswatch_theme"

    def run(self, *args):
        """Given a swatch name and a parent theme, creates a custom theme."""

        parser = OptionParser()
        parser.add_option("-n", "--name", dest="name",
            help="New theme name (default: custom)", default='custom')
        parser.add_option("-s", "--swatch", dest="swatch",
            help="Name of the swatch from bootswatch.com (default: slate)",
            default='slate')
        parser.add_option("-p", "--parent", dest="parent",
            help="Parent theme name (default: site)", default='site')
        (options, args) = parser.parse_args(list(args))

        name = options.name
        swatch = options.swatch
        parent = options.parent

        print "Creating '%s' theme from '%s' and '%s'" % (
            name, swatch, parent)
        try:
            os.makedirs(os.path.join('themes', name, 'assets', 'css'))
        except:
            pass
        for fname in ('bootstrap.min.css', 'bootstrap.css'):
            url = 'http://bootswatch.com/%s/%s' % (swatch, fname)
            print "Downloading: ", url
            data = urllib2.urlopen(url).read()
            with open(os.path.join(
                'themes', name, 'assets', 'css', fname), 'wb+') as output:
                output.write(data)

        with open(os.path.join('themes', name, 'parent'), 'wb+') as output:
            output.write(parent)
        print 'Theme created. Change the THEME setting to "%s" to use it.'\
            % name
