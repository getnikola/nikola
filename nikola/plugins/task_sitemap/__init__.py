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

from __future__ import print_function, absolute_import
import os
import sys
import tempfile

from nikola.plugin_categories import LateTask
from nikola.utils import config_changed

from nikola.plugins.task_sitemap import sitemap_gen


class Sitemap(LateTask):
    """Copy theme assets into output."""

    name = "sitemap"

    def gen_tasks(self):
        if sys.version_info[0] == 3:
            print("sitemap generation is not available for python 3")
            yield {
                'basename': 'sitemap',
                'name': 'sitemap',
                'actions': [],
            }
            return
        """Generate Google sitemap."""
        kw = {
            "blog_url": self.site.config["BLOG_URL"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
        }
        output_path = os.path.abspath(kw['output_folder'])
        sitemap_path = os.path.join(output_path, "sitemap.xml.gz")

        def sitemap():
            # Generate config
            config_data = """<?xml version="1.0" encoding="UTF-8"?>
    <site
    base_url="%s"
    store_into="%s"
    verbose="1" >
    <directory path="%s" url="%s" />
    <filter action="drop" type="wildcard" pattern="*~" />
    <filter action="drop" type="regexp" pattern="/\.[^/]*" />
    </site>""" % (
                kw["blog_url"],
                sitemap_path,
                output_path,
                kw["blog_url"],
            )
            config_file = tempfile.NamedTemporaryFile(delete=False)
            config_file.write(config_data.encode('utf8'))
            config_file.close()

            # Generate sitemap
            sitemap = sitemap_gen.CreateSitemapFromFile(config_file.name, True)
            if not sitemap:
                sitemap_gen.output.Log('Configuration file errors -- exiting.',
                                       0)
            else:
                sitemap.Generate()
                sitemap_gen.output.Log('Number of errors: %d' %
                                       sitemap_gen.output.num_errors, 1)
                sitemap_gen.output.Log('Number of warnings: %d' %
                                       sitemap_gen.output.num_warns, 1)
            os.unlink(config_file.name)

        yield {
            "basename": "sitemap",
            "targets": [sitemap_path],
            "actions": [(sitemap,)],
            "uptodate": [config_changed(kw)],
            "clean": True,
        }
