# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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
import os
import re
import sys
try:
    from urllib import unquote
    from urlparse import urlparse, urljoin, urldefrag
except ImportError:
    from urllib.parse import unquote, urlparse, urljoin, urldefrag  # NOQA

import lxml.html

from nikola.plugin_categories import Command
from nikola.utils import get_logger


def _call_nikola_list(l, site, arguments):
    class NotReallyAStream(object):
        """A massive hack."""
        out = []

        def write(self, t):
            self.out.append(t)

    oldstream = l.outstream
    newstream = NotReallyAStream()
    try:
        l.outstream = newstream
        l.parse_execute(arguments)
        return newstream.out
    finally:
        l.outstream = oldstream


def real_scan_files(l, site):
    task_fnames = set([])
    real_fnames = set([])
    output_folder = site.config['OUTPUT_FOLDER']
    # First check that all targets are generated in the right places
    for task in _call_nikola_list(l, site, ["--all"]):
        task = task.strip()
        if output_folder in task and ':' in task:
            fname = task.split(':', 1)[-1]
            task_fnames.add(fname)
    # And now check that there are no non-target files
    for root, dirs, files in os.walk(output_folder, followlinks=True):
        for src_name in files:
            fname = os.path.join(root, src_name)
            real_fnames.add(fname)

    only_on_output = list(real_fnames - task_fnames)

    only_on_input = list(task_fnames - real_fnames)

    return (only_on_output, only_on_input)


def fs_relpath_from_url_path(url_path):
    """Expects as input an urlparse(s).path"""
    url_path = unquote(url_path)
    # in windows relative paths don't begin with os.sep
    if sys.platform == 'win32' and len(url_path):
        url_path = url_path.replace('/', '\\')
    return url_path


class CommandCheck(Command):
    """Check the generated site."""

    name = "check"
    logger = None

    doc_usage = "-l [--find-sources] | -f"
    doc_purpose = "check links and files in the generated site"
    cmd_options = [
        {
            'name': 'links',
            'short': 'l',
            'long': 'check-links',
            'type': bool,
            'default': False,
            'help': 'Check for dangling links',
        },
        {
            'name': 'files',
            'short': 'f',
            'long': 'check-files',
            'type': bool,
            'default': False,
            'help': 'Check for unknown (orphaned and not generated) files',
        },
        {
            'name': 'clean',
            'long': 'clean-files',
            'type': bool,
            'default': False,
            'help': 'Remove all unknown files, use with caution',
        },
        {
            'name': 'find_sources',
            'long': 'find-sources',
            'type': bool,
            'default': False,
            'help': 'List possible source files for files with broken links.',
        },
        {
            'name': 'verbose',
            'long': 'verbose',
            'short': 'v',
            'type': bool,
            'default': False,
            'help': 'Be more verbose.',
        },
    ]

    def _execute(self, options, args):
        """Check the generated site."""
        self.logger = get_logger('check', self.site.loghandlers)
        self.l = self._doitargs['cmds'].get_plugin('list')(config=self.config, **self._doitargs)

        if not options['links'] and not options['files'] and not options['clean']:
            print(self.help())
            return False
        if options['verbose']:
            self.logger.level = 1
        else:
            self.logger.level = 4
        if options['links']:
            failure = self.scan_links(options['find_sources'])
        if options['files']:
            failure = self.scan_files()
        if options['clean']:
            failure = self.clean_files()
        if failure:
            sys.exit(1)

    existing_targets = set([])

    def analyze(self, task, find_sources=False):
        rv = False
        self.whitelist = [re.compile(x) for x in self.site.config['LINK_CHECK_WHITELIST']]
        base_url = urlparse(self.site.config['BASE_URL'])
        self.existing_targets.add(self.site.config['SITE_URL'])
        self.existing_targets.add(self.site.config['BASE_URL'])
        url_type = self.site.config['URL_TYPE']
        if url_type in ('absolute', 'full_path'):
            url_netloc_to_root = urlparse(self.site.config['BASE_URL']).path
        try:
            filename = task.split(":")[-1]

            if filename.startswith(self.site.config['CACHE_FOLDER']):
                # Do not look at links in the cache, which are not parsed by
                # anyone and may result in false positives.  Problems arise
                # with galleries, for example.  Full rationale: (Issue #1447)
                self.logger.notice("Ignoring {0} (in cache, links may be incorrect)".format(filename))
                return False

            d = lxml.html.fromstring(open(filename, 'rb').read())
            for l in d.iterlinks():
                target = l[0].attrib[l[1]]
                if target == "#":
                    continue
                target, _ = urldefrag(target)
                parsed = urlparse(target)

                # Warn about links from https to http (mixed-security)
                if base_url.netloc == parsed.netloc and base_url.scheme == "https" and parsed.scheme == "http":
                    self.logger.warn("Mixed-content security for link in {0}: {1}".format(filename, target))

                # Absolute links when using only paths, skip.
                if (parsed.scheme or target.startswith('//')) and url_type in ('rel_path', 'full_path'):
                    continue

                # Absolute links to other domains, skip
                if (parsed.scheme or target.startswith('//')) and parsed.netloc != base_url.netloc:
                    continue

                if url_type == 'rel_path':
                    target_filename = os.path.abspath(
                        os.path.join(os.path.dirname(filename), unquote(target)))

                elif url_type in ('full_path', 'absolute'):
                    if url_type == 'absolute':
                        # convert to 'full_path' case, ie url relative to root
                        url_rel_path = parsed.path[len(url_netloc_to_root):]
                    else:
                        # convert to relative to base path
                        url_rel_path = target[len(url_netloc_to_root):]
                    if url_rel_path == '' or url_rel_path.endswith('/'):
                        url_rel_path = urljoin(url_rel_path, self.site.config['INDEX_FILE'])
                    fs_rel_path = fs_relpath_from_url_path(url_rel_path)
                    target_filename = os.path.join(self.site.config['OUTPUT_FOLDER'], fs_rel_path)

                if any(re.search(x, target_filename) for x in self.whitelist):
                    continue
                elif target_filename not in self.existing_targets:
                    if os.path.exists(target_filename):
                        self.logger.notice("Good link {0} => {1}".format(target, target_filename))
                        self.existing_targets.add(target_filename)
                    else:
                        rv = True
                        self.logger.warn("Broken link in {0}: {1}".format(filename, target))
                        if find_sources:
                            self.logger.warn("Possible sources:")
                            self.logger.warn("\n".join(_call_nikola_list(self.l, self.site, ["--deps", task])))
                            self.logger.warn("===============================\n")
        except Exception as exc:
            self.logger.error("Error with: {0} {1}".format(filename, exc))
        return rv

    def scan_links(self, find_sources=False):
        self.logger.info("Checking Links:")
        self.logger.info("===============\n")
        self.logger.notice("{0} mode".format(self.site.config['URL_TYPE']))
        failure = False
        for task in _call_nikola_list(self.l, self.site, ["--all"]):
            task = task.strip()
            if task.split(':')[0] in (
                    'render_tags', 'render_archive',
                    'render_galleries', 'render_indexes',
                    'render_pages', 'render_posts',
                    'render_site') and '.html' in task:
                if self.analyze(task, find_sources):
                    failure = True
        if not failure:
            self.logger.info("All links checked.")
        return failure

    def scan_files(self):
        failure = False
        self.logger.info("Checking Files:")
        self.logger.info("===============\n")
        only_on_output, only_on_input = real_scan_files(self.l, self.site)

        # Ignore folders
        only_on_output = [p for p in only_on_output if not os.path.isdir(p)]
        only_on_input = [p for p in only_on_input if not os.path.isdir(p)]

        if only_on_output:
            only_on_output.sort()
            self.logger.warn("Files from unknown origins (orphans):")
            for f in only_on_output:
                self.logger.warn(f)
            failure = True
        if only_on_input:
            only_on_input.sort()
            self.logger.warn("Files not generated:")
            for f in only_on_input:
                self.logger.warn(f)
        if not failure:
            self.logger.info("All files checked.")
        return failure

    def clean_files(self):
        only_on_output, _ = real_scan_files(self.l, self.site)
        for f in only_on_output:
            os.unlink(f)
        return True
