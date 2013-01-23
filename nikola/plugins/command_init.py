# Copyright (c) 2012 Roberto Alsina y otros.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function
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
    "textile": ('.textile',),
    "txt2tags": ('.t2t',),
    "bbcode": ('.bb',),
    "wiki": ('.wiki',),
    "html": ('.html', '.htm')
    }""",
        'REDIRECTIONS': '[]',
        }

    def run(self, *args):
        """Create a new site."""
        parser = OptionParser(usage=self.usage)
        (options, args) = parser.parse_args(list(args))

        if not args:
            print("Usage: nikola init folder [options]")
            return
        target = args[0]
        if target is None:
            print(self.usage)
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

            print("A new site with some sample data has been created at %s."
                % target)
            print("See README.txt in that folder for more information.")
