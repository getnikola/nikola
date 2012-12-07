from optparse import OptionParser
import os
import shutil
import codecs

from mako.template import Template

import nikola
from nikola.plugin_categories import Command


class CommandInit(Command):
    """Create a new site."""

    name = "init"

    usage = """Usage: nikola init folder [options].

That will create a sample site in the specified folder.
The destination folder must not exist.
"""

    SAMPLE_CONF = {
        'BLOG_AUTHOR': "Your Name",
        'BLOG_TITLE': "Demo Site",
        'BLOG_URL': "http://nikola.ralsina.com.ar",
        'BLOG_EMAIL': "joe@demo.site",
        'BLOG_DESCRIPTION': "This is a demo site for Nikola.",
        'DEFAULT_LANG': "en",

        'POST_PAGES': """(
    ("posts/*.txt", "posts", "post.tmpl", True),
    ("stories/*.txt", "stories", "story.tmpl", False),
)""",

        'POST_COMPILERS': """{
    "rest": ('.txt', '.rst'),
    "markdown": ('.md', '.mdown', '.markdown'),
    "html": ('.html', '.htm')
    }""",
        }

    def run(self, *args):
        """Create a new site."""
        parser = OptionParser(usage=self.usage)
        (options, args) = parser.parse_args(list(args))

        target = args[0]
        if target is None:
            print self.usage
        else:
            # copy sample data
            lib_path = os.path.dirname(nikola.__file__)
            src = os.path.join(lib_path, 'data', 'samplesite')
            shutil.copytree(src, target)
            # create conf.py
            template_path = os.path.join(lib_path, 'conf.py.in')
            conf_template = Template(filename=template_path)
            conf_path = os.path.join(target, 'conf.py')
            with codecs.open(conf_path, 'w+', 'utf8') as fd:
                fd.write(conf_template.render(**self.SAMPLE_CONF))

            print "A new site with some sample data has been created at %s."\
                % target
            print "See README.txt in that folder for more information."
