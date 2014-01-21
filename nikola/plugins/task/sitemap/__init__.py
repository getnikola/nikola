# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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
    from urlparse import urljoin, urlparse
except ImportError:
    from urllib.parse import urljoin, urlparse  # NOQA

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
 </url>
"""

get_lastmod = lambda p: datetime.datetime.fromtimestamp(os.stat(p).st_mtime).isoformat().split('T')[0]


def get_base_path(base):
    """returns the path of a base URL if it contains one.

    >>> get_base_path('http://some.site') == '/'
    True
    >>> get_base_path('http://some.site/') == '/'
    True
    >>> get_base_path('http://some.site/some/sub-path') == '/some/sub-path/'
    True
    >>> get_base_path('http://some.site/some/sub-path/') == '/some/sub-path/'
    True
    """
    # first parse the base_url for some path
    base_parsed = urlparse(base)

    if not base_parsed.path:
        sub_path = ''
    else:
        sub_path = base_parsed.path
    if sub_path.endswith('/'):
        return sub_path
    else:
        return sub_path + '/'


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
            "mapped_extensions": self.site.config.get('MAPPED_EXTENSIONS', ['.html', '.htm', '.xml'])
        }
        output_path = kw['output_folder']
        sitemap_path = os.path.join(output_path, "sitemap.xml")
        base_path = get_base_path(kw['base_url'])
        locs = {}

        output = kw['output_folder']
        base_url = kw['base_url']
        mapped_exts = kw['mapped_extensions']

        def scan_locs():
            for root, dirs, files in os.walk(output):
                if not dirs and not files and not kw['sitemap_include_fileless_dirs']:
                    continue  # Totally empty, not on sitemap
                path = os.path.relpath(root, output)
                # ignore the current directory.
                path = (path.replace(os.sep, '/') + '/').replace('./', '')
                lastmod = get_lastmod(root)
                loc = urljoin(base_url, (base_path + path).lstrip('/'))
                if kw['index_file'] in files and kw['strip_indexes']:  # ignore folders when not stripping urls
                    locs[loc] = url_format.format(loc, lastmod)
                for fname in files:
                    if kw['strip_indexes'] and fname == kw['index_file']:
                        continue  # We already mapped the folder
                    if os.path.splitext(fname)[-1] in mapped_exts:
                        real_path = os.path.join(root, fname)
                        path = os.path.relpath(real_path, output)
                        if path.endswith(kw['index_file']) and kw['strip_indexes']:
                            # ignore index files when stripping urls
                            continue
                        if path.endswith('.html') or path.endswith('.htm'):
                            if not u'<!doctype html' in codecs.open(real_path, 'r', 'utf8').read(1024).lower():
                                # ignores "html" files without doctype
                                # alexa-verify, google-site-verification, etc.
                                continue
                        if path.endswith('.xml'):
                            if not u'<rss' in codecs.open(real_path, 'r', 'utf8').read(512):
                                # ignores all XML files except those presumed to be RSS
                                continue
                        post = self.site.post_per_file.get(path)
                        if post and (post.is_draft or post.is_retired or post.publish_later):
                            continue
                        path = path.replace(os.sep, '/')
                        lastmod = get_lastmod(real_path)
                        loc = urljoin(base_url, (base_path + path).lstrip('/'))
                        locs[loc] = url_format.format(loc, lastmod)

        def write_sitemap():
            # Have to rescan, because files may have been added between
            # task dep scanning and task execution
            scan_locs()
            with codecs.open(sitemap_path, 'wb+', 'utf8') as outf:
                outf.write(header)
                for k in sorted(locs.keys()):
                    outf.write(locs[k])
                outf.write("</urlset>")
            # Other tasks can depend on this output, instead of having
            # to scan locations.
            return {'locations': list(locs.keys())}

        scan_locs()
        yield self.group_task()
        task = {
            "basename": "sitemap",
            "name": sitemap_path,
            "targets": [sitemap_path],
            "actions": [(write_sitemap,)],
            "uptodate": [config_changed({1: kw, 2: locs})],
            "clean": True,
            "task_dep": ["render_site"],
        }
        yield task

if __name__ == '__main__':
    import doctest
    doctest.testmod()
