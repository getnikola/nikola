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

from __future__ import print_function, absolute_import, unicode_literals
import codecs
import datetime
import os
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA

from nikola.plugin_categories import LateTask
from nikola.utils import config_changed


header = """<?xml version="1.0" encoding="UTF-8"?>
<urlset
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
                        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
"""

url_format = """ <url>
  <loc>{0}</loc>
  <lastmod>{1}</lastmod>
  <priority>0.5000</priority>
 </url>
"""

get_lastmod = lambda p: datetime.datetime.fromtimestamp(os.stat(p).st_mtime).isoformat().split('T')[0]


class Sitemap(LateTask):
    """Generate google sitemap."""

    name = "sitemap"

    def gen_tasks(self):
        """Generate Google sitemap."""
        kw = {
            "base_url": self.site.config["BASE_URL"],
            "site_url": self.site.config["SITE_URL"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "strip_indexes": self.site.config["STRIP_INDEXES"],
            "index_file": self.site.config["INDEX_FILE"],
            "sitemap_include_fileless_dirs": self.site.config["SITEMAP_INCLUDE_FILELESS_DIRS"],
            "mapped_extensions": self.site.config.get('MAPPED_EXTENSIONS', ['.html', '.htm'])
        }
        output_path = kw['output_folder']
        sitemap_path = os.path.join(output_path, "sitemap.xml")
        locs = {}

        def write_sitemap():
            with codecs.open(sitemap_path, 'wb+', 'utf8') as outf:
                outf.write(header)
                for k in sorted(locs.keys()):
                    outf.write(locs[k])
                outf.write("</urlset>")
            return True

        output = kw['output_folder']
        base_url = kw['base_url']
        mapped_exts = kw['mapped_extensions']
        for root, dirs, files in os.walk(output):
            if not dirs and not files and not kw['sitemap_include_fileless_dirs']:
                continue  # Totally empty, not on sitemap
            path = os.path.relpath(root, output)
            path = path.replace(os.sep, '/') + '/'
            lastmod = get_lastmod(root)
            loc = urljoin(base_url, path)
            if 'index.html' in files:  # Only map folders with indexes
                locs[loc] = url_format.format(loc, lastmod)
            for fname in files:
                if kw['strip_indexes'] and fname == kw['index_file']:
                    continue  # We already mapped the folder
                if os.path.splitext(fname)[-1] in mapped_exts:
                    real_path = os.path.join(root, fname)
                    path = os.path.relpath(real_path, output)
                    path = path.replace(os.sep, '/')
                    lastmod = get_lastmod(real_path)
                    loc = urljoin(base_url, path)
                    locs[loc] = url_format.format(loc, lastmod)
        task = {
            "basename": "sitemap",
            "name": sitemap_path,
            "targets": [sitemap_path],
            "actions": [(write_sitemap,)],
            "uptodate": [config_changed({1: kw, 2: locs})],
            "clean": True,
        }
        yield task
