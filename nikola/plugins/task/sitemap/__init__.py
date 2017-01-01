# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Generate a sitemap."""

from __future__ import print_function, absolute_import, unicode_literals
import io
import datetime
import dateutil.tz
import os
import sys
try:
    from urlparse import urljoin, urlparse
    import robotparser as robotparser
except ImportError:
    from urllib.parse import urljoin, urlparse  # NOQA
    import urllib.robotparser as robotparser  # NOQA

from nikola.plugin_categories import LateTask
from nikola.utils import apply_filters, config_changed, encodelink


urlset_header = """<?xml version="1.0" encoding="UTF-8"?>
<urlset
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    xmlns:xhtml="http://www.w3.org/1999/xhtml"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
                        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
"""

loc_format = """ <url>
  <loc>{0}</loc>
  <lastmod>{1}</lastmod>{2}
 </url>
"""

urlset_footer = "</urlset>"

sitemapindex_header = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    xmlns:xhtml="http://www.w3.org/1999/xhtml"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
                        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
"""

sitemap_format = """ <sitemap>
  <loc>{0}</loc>
  <lastmod>{1}</lastmod>
 </sitemap>
"""

alternates_format = """\n  <xhtml:link rel="alternate" hreflang="{0}" href="{1}" />"""


sitemapindex_footer = "</sitemapindex>"


def get_base_path(base):
    """Return the path of a base URL if it contains one.

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
    """Generate a sitemap."""

    name = "sitemap"

    def gen_tasks(self):
        """Generate a sitemap."""
        kw = {
            "base_url": self.site.config["BASE_URL"],
            "site_url": self.site.config["SITE_URL"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "strip_indexes": self.site.config["STRIP_INDEXES"],
            "index_file": self.site.config["INDEX_FILE"],
            "sitemap_include_fileless_dirs": self.site.config["SITEMAP_INCLUDE_FILELESS_DIRS"],
            "mapped_extensions": self.site.config.get('MAPPED_EXTENSIONS', ['.atom', '.html', '.htm', '.php', '.xml', '.rss']),
            "robots_exclusions": self.site.config["ROBOTS_EXCLUSIONS"],
            "filters": self.site.config["FILTERS"],
            "translations": self.site.config["TRANSLATIONS"],
            "tzinfo": self.site.config['__tzinfo__'],
            "sitemap_plugin_revision": 1,
        }

        output = kw['output_folder']
        base_url = kw['base_url']
        mapped_exts = kw['mapped_extensions']

        output_path = kw['output_folder']
        sitemapindex_path = os.path.join(output_path, "sitemapindex.xml")
        sitemap_path = os.path.join(output_path, "sitemap.xml")
        base_path = get_base_path(kw['base_url'])
        sitemapindex = {}
        urlset = {}

        def scan_locs():
            """Scan site locations."""
            for root, dirs, files in os.walk(output, followlinks=True):
                if not dirs and not files and not kw['sitemap_include_fileless_dirs']:
                    continue  # Totally empty, not on sitemap
                path = os.path.relpath(root, output)
                # ignore the current directory.
                if path == '.':
                    path = ''
                else:
                    path = path.replace(os.sep, '/') + '/'
                lastmod = self.get_lastmod(root)
                loc = urljoin(base_url, base_path + path)
                if kw['index_file'] in files and kw['strip_indexes']:  # ignore folders when not stripping urls
                    post = self.site.post_per_file.get(path + kw['index_file'])
                    if post and (post.is_draft or post.is_private or post.publish_later):
                        continue
                    alternates = []
                    if post:
                        for lang in post.translated_to:
                            alt_url = post.permalink(lang=lang, absolute=True)
                            if encodelink(loc) == alt_url:
                                continue
                            alternates.append(alternates_format.format(lang, alt_url))
                    urlset[loc] = loc_format.format(encodelink(loc), lastmod, ''.join(alternates))
                for fname in files:
                    if kw['strip_indexes'] and fname == kw['index_file']:
                        continue  # We already mapped the folder
                    if os.path.splitext(fname)[-1] in mapped_exts:
                        real_path = os.path.join(root, fname)
                        path = os.path.relpath(real_path, output)
                        if path.endswith(kw['index_file']) and kw['strip_indexes']:
                            # ignore index files when stripping urls
                            continue
                        if not robot_fetch(path):
                            continue

                        # read in binary mode to make ancient files work
                        fh = open(real_path, 'rb')
                        filehead = fh.read(1024)
                        fh.close()

                        if path.endswith('.html') or path.endswith('.htm') or path.endswith('.php'):
                            """ ignores "html" files without doctype """
                            if b'<!doctype html' not in filehead.lower():
                                continue

                            """ ignores "html" files with noindex robot directives """
                            robots_directives = [b'<meta content=noindex name=robots',
                                                 b'<meta content=none name=robots',
                                                 b'<meta name=robots content=noindex',
                                                 b'<meta name=robots content=none']
                            lowquothead = filehead.lower().decode('utf-8', 'ignore').replace('"', '').encode('utf-8')
                            if any([robot_directive in lowquothead for robot_directive in robots_directives]):
                                continue

                        # put Atom and RSS in sitemapindex[] instead of in urlset[],
                        # sitemap_path is included after it is generated
                        if path.endswith('.xml') or path.endswith('.atom') or path.endswith('.rss'):
                            known_elm_roots = (b'<feed', b'<rss', b'<urlset')
                            if any([elm_root in filehead.lower() for elm_root in known_elm_roots]) and path != sitemap_path:
                                path = path.replace(os.sep, '/')
                                lastmod = self.get_lastmod(real_path)
                                loc = urljoin(base_url, base_path + path)
                                sitemapindex[loc] = sitemap_format.format(encodelink(loc), lastmod)
                                continue
                            else:
                                continue  # ignores all XML files except those presumed to be RSS
                        post = self.site.post_per_file.get(path)
                        if post and (post.is_draft or post.is_private or post.publish_later):
                            continue
                        path = path.replace(os.sep, '/')
                        lastmod = self.get_lastmod(real_path)
                        loc = urljoin(base_url, base_path + path)
                        alternates = []
                        if post:
                            for lang in post.translated_to:
                                alt_url = post.permalink(lang=lang, absolute=True)
                                if encodelink(loc) == alt_url:
                                    continue
                                alternates.append(alternates_format.format(lang, alt_url))
                        urlset[loc] = loc_format.format(encodelink(loc), lastmod, '\n'.join(alternates))

        def robot_fetch(path):
            """Check if robots can fetch a file."""
            for rule in kw["robots_exclusions"]:
                robot = robotparser.RobotFileParser()
                robot.parse(["User-Agent: *", "Disallow: {0}".format(rule)])
                if sys.version_info[0] == 3:
                    if not robot.can_fetch("*", '/' + path):
                        return False  # not robot food
                else:
                    if not robot.can_fetch("*", ('/' + path).encode('utf-8')):
                        return False  # not robot food
            return True

        def write_sitemap():
            """Write sitemap to file."""
            # Have to rescan, because files may have been added between
            # task dep scanning and task execution
            with io.open(sitemap_path, 'w+', encoding='utf8') as outf:
                outf.write(urlset_header)
                for k in sorted(urlset.keys()):
                    outf.write(urlset[k])
                outf.write(urlset_footer)
            sitemap_url = urljoin(base_url, base_path + "sitemap.xml")
            sitemapindex[sitemap_url] = sitemap_format.format(sitemap_url, self.get_lastmod(sitemap_path))

        def write_sitemapindex():
            """Write sitemap index."""
            with io.open(sitemapindex_path, 'w+', encoding='utf8') as outf:
                outf.write(sitemapindex_header)
                for k in sorted(sitemapindex.keys()):
                    outf.write(sitemapindex[k])
                outf.write(sitemapindex_footer)

        def scan_locs_task():
            """Yield a task to calculate the dependencies of the sitemap.

            Other tasks can depend on this output, instead of having
            to scan locations.
            """
            scan_locs()

            # Generate a list of file dependencies for the actual generation
            # task, so rebuilds are triggered.  (Issue #1032)
            output = kw["output_folder"]
            file_dep = []

            for i in urlset.keys():
                p = os.path.join(output, urlparse(i).path.replace(base_path, '', 1))
                if not p.endswith('sitemap.xml') and not os.path.isdir(p):
                    file_dep.append(p)
                if os.path.isdir(p) and os.path.exists(os.path.join(p, 'index.html')):
                    file_dep.append(p + 'index.html')

            for i in sitemapindex.keys():
                p = os.path.join(output, urlparse(i).path.replace(base_path, '', 1))
                if not p.endswith('sitemap.xml') and not os.path.isdir(p):
                    file_dep.append(p)
                if os.path.isdir(p) and os.path.exists(os.path.join(p, 'index.html')):
                    file_dep.append(p + 'index.html')

            return {'file_dep': file_dep}

        yield {
            "basename": "_scan_locs",
            "name": "sitemap",
            "actions": [(scan_locs_task)]
        }

        yield self.group_task()
        yield apply_filters({
            "basename": "sitemap",
            "name": sitemap_path,
            "targets": [sitemap_path],
            "actions": [(write_sitemap,)],
            "uptodate": [config_changed(kw, 'nikola.plugins.task.sitemap:write')],
            "clean": True,
            "task_dep": ["render_site"],
            "calc_dep": ["_scan_locs:sitemap"],
        }, kw['filters'])
        yield apply_filters({
            "basename": "sitemap",
            "name": sitemapindex_path,
            "targets": [sitemapindex_path],
            "actions": [(write_sitemapindex,)],
            "uptodate": [config_changed(kw, 'nikola.plugins.task.sitemap:write_index')],
            "clean": True,
            "file_dep": [sitemap_path]
        }, kw['filters'])

    def get_lastmod(self, p):
        """Get last modification date."""
        if self.site.invariant:
            return '2038-01-01'
        else:
            # RFC 3339 (web ISO 8601 profile) represented in UTC with Zulu
            # zone desgignator as recommeded for sitemaps. Second and
            # microsecond precision is stripped for compatibility.
            lastmod = datetime.datetime.utcfromtimestamp(os.stat(p).st_mtime).replace(tzinfo=dateutil.tz.gettz('UTC'), second=0, microsecond=0).isoformat().replace('+00:00', 'Z')
            return lastmod


if __name__ == '__main__':
    import doctest
    doctest.testmod()
