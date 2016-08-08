# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Check the generated site."""

from __future__ import print_function
from collections import defaultdict
import os
import re
import sys
import time
import logbook
try:
    from urllib import unquote
    from urlparse import urlparse, urljoin, urldefrag
except ImportError:
    from urllib.parse import unquote, urlparse, urljoin, urldefrag  # NOQA

from doit.loader import generate_tasks
import lxml.html
import requests

from nikola.plugin_categories import Command
from nikola.utils import get_logger, STDERR_HANDLER


def _call_nikola_list(site, cache=None):
    if cache is not None:
        if 'files' in cache and 'deps' in cache:
            return cache['files'], cache['deps']
    files = []
    deps = defaultdict(list)
    for task in generate_tasks('render_site', site.gen_tasks('render_site', "Task", '')):
        files.extend(task.targets)
        for target in task.targets:
            deps[target].extend(task.file_dep)
    for task in generate_tasks('post_render', site.gen_tasks('render_site', "LateTask", '')):
        files.extend(task.targets)
        for target in task.targets:
            deps[target].extend(task.file_dep)
    if cache is not None:
        cache['files'] = files
        cache['deps'] = deps
    return files, deps


def real_scan_files(site, cache=None):
    """Scan for files."""
    task_fnames = set([])
    real_fnames = set([])
    output_folder = site.config['OUTPUT_FOLDER']
    # First check that all targets are generated in the right places
    for fname in _call_nikola_list(site, cache)[0]:
        fname = fname.strip()
        if fname.startswith(output_folder):
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
    """Create a filesystem relative path from an URL path."""
    # Expects as input an urlparse(s).path
    url_path = unquote(url_path)
    # in windows relative paths don't begin with os.sep
    if sys.platform == 'win32' and len(url_path):
        url_path = url_path.replace('/', '\\')
    return url_path


class CommandCheck(Command):
    """Check the generated site."""

    name = "check"
    logger = None

    doc_usage = "[-v] (-l [--find-sources] [-r] | -f [--clean-files])"
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
        {
            'name': 'remote',
            'long': 'remote',
            'short': 'r',
            'type': bool,
            'default': False,
            'help': 'Check that remote links work.',
        },
    ]

    def _execute(self, options, args):
        """Check the generated site."""
        self.logger = get_logger('check', STDERR_HANDLER)

        if not options['links'] and not options['files'] and not options['clean']:
            print(self.help())
            return False
        if options['verbose']:
            self.logger.level = logbook.DEBUG
        else:
            self.logger.level = logbook.NOTICE
        failure = False
        if options['links']:
            failure |= self.scan_links(options['find_sources'], options['remote'])
        if options['files']:
            failure |= self.scan_files()
        if options['clean']:
            failure |= self.clean_files()
        if failure:
            return 1

    existing_targets = set([])
    checked_remote_targets = {}
    cache = {}

    def analyze(self, fname, find_sources=False, check_remote=False):
        """Analyze links on a page."""
        rv = False
        self.whitelist = [re.compile(x) for x in self.site.config['LINK_CHECK_WHITELIST']]
        self.internal_redirects = [urljoin('/', _[0]) for _ in self.site.config['REDIRECTIONS']]
        base_url = urlparse(self.site.config['BASE_URL'])
        self.existing_targets.add(self.site.config['SITE_URL'])
        self.existing_targets.add(self.site.config['BASE_URL'])
        url_type = self.site.config['URL_TYPE']

        deps = {}
        if find_sources:
            deps = _call_nikola_list(self.site, self.cache)[1]

        if url_type in ('absolute', 'full_path'):
            url_netloc_to_root = urlparse(self.site.config['BASE_URL']).path
        try:
            filename = fname

            if filename.startswith(self.site.config['CACHE_FOLDER']):
                # Do not look at links in the cache, which are not parsed by
                # anyone and may result in false positives.  Problems arise
                # with galleries, for example.  Full rationale: (Issue #1447)
                self.logger.notice("Ignoring {0} (in cache, links may be incorrect)".format(filename))
                return False

            if not os.path.exists(fname):
                # Quietly ignore files that don’t exist; use `nikola check -f` instead (Issue #1831)
                return False

            if '.html' == fname[-5:]:
                d = lxml.html.fromstring(open(filename, 'rb').read())
                extra_objs = lxml.html.fromstring('<html/>')

                # Turn elements with a srcset attribute into individual img elements with src attributes
                for obj in list(d.xpath('(*//img|*//source)')):
                    if 'srcset' in obj.attrib:
                        for srcset_item in obj.attrib['srcset'].split(','):
                            extra_objs.append(lxml.etree.Element('img', src=srcset_item.strip().split(' ')[0]))
                link_elements = list(d.iterlinks()) + list(extra_objs.iterlinks())
            # Extract links from XML formats to minimal HTML, allowing those to go through the link checks
            elif '.atom' == filename[-5:]:
                d = lxml.etree.parse(filename)
                link_elements = lxml.html.fromstring('<html/>')
                for elm in d.findall('*//{http://www.w3.org/2005/Atom}link'):
                    feed_link = elm.attrib['href'].split('?')[0].strip()  # strip FEED_LINKS_APPEND_QUERY
                    link_elements.append(lxml.etree.Element('a', href=feed_link))
                link_elements = list(link_elements.iterlinks())
            elif filename.endswith('sitemap.xml') or filename.endswith('sitemapindex.xml'):
                d = lxml.etree.parse(filename)
                link_elements = lxml.html.fromstring('<html/>')
                for elm in d.getroot().findall("*//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                    link_elements.append(lxml.etree.Element('a', href=elm.text.strip()))
                link_elements = list(link_elements.iterlinks())
            else:  # unsupported file type
                return False

            for l in link_elements:
                target = l[2]
                if target == "#":
                    continue
                target = urldefrag(target)[0]

                if any([urlparse(target).netloc.endswith(_) for _ in ['example.com', 'example.net', 'example.org']]):
                    self.logger.debug("Not testing example address \"{0}\".".format(target))
                    continue

                # absolute URL to root-relative
                if target.startswith(base_url.geturl()):
                    target = target.replace(base_url.geturl(), '/')

                parsed = urlparse(target)

                # Warn about links from https to http (mixed-security)
                if base_url.netloc == parsed.netloc and base_url.scheme == "https" and parsed.scheme == "http":
                    self.logger.warn("Mixed-content security for link in {0}: {1}".format(filename, target))

                # Link to an internal REDIRECTIONS page
                if target in self.internal_redirects:
                    redir_status_code = 301
                    redir_target = [_dest for _target, _dest in self.site.config['REDIRECTIONS'] if urljoin('/', _target) == target][0]
                    self.logger.warn("Remote link moved PERMANENTLY to \"{0}\" and should be updated in {1}: {2} [HTTP: 301]".format(redir_target, filename, target))

                # Absolute links to other domains, skip
                # Absolute links when using only paths, skip.
                if ((parsed.scheme or target.startswith('//')) and parsed.netloc != base_url.netloc) or \
                        ((parsed.scheme or target.startswith('//')) and url_type in ('rel_path', 'full_path')):
                    if not check_remote or parsed.scheme not in ["http", "https"]:
                        continue
                    if target in self.checked_remote_targets:  # already checked this exact target
                        if self.checked_remote_targets[target] in [301, 308]:
                            self.logger.warn("Remote link PERMANENTLY redirected in {0}: {1} [Error {2}]".format(filename, target, self.checked_remote_targets[target]))
                        elif self.checked_remote_targets[target] in [302, 307]:
                            self.logger.debug("Remote link temporarily redirected in {0}: {1} [HTTP: {2}]".format(filename, target, self.checked_remote_targets[target]))
                        elif self.checked_remote_targets[target] > 399:
                            self.logger.error("Broken link in {0}: {1} [Error {2}]".format(filename, target, self.checked_remote_targets[target]))
                        continue

                    # Skip whitelisted targets
                    if any(re.search(_, target) for _ in self.whitelist):
                        continue

                    # Check the remote link works
                    req_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0 (Nikola)'}  # I’m a real boy!
                    resp = requests.head(target, headers=req_headers, allow_redirects=False)

                    # Retry client errors (4xx) as GET requests because many servers are broken
                    if resp.status_code >= 400 and resp.status_code <= 499:
                        time.sleep(0.5)
                        resp = requests.get(target, headers=req_headers, allow_redirects=False)

                    # Follow redirects and see where they lead, redirects to errors will be reported twice
                    if resp.status_code in [301, 302, 307, 308]:
                        redir_status_code = resp.status_code
                        time.sleep(0.5)
                        # Known redirects are retested using GET because IIS servers otherwise get HEADaches
                        resp = requests.get(target, headers=req_headers, allow_redirects=True)
                        # Permanent redirects should be updated
                        if redir_status_code in [301, 308]:
                            self.logger.warn("Remote link moved PERMANENTLY to \"{0}\" and should be updated in {1}: {2} [HTTP: {3}]".format(resp.url, filename, target, redir_status_code))
                        if redir_status_code in [302, 307]:
                            self.logger.debug("Remote link temporarily redirected to \"{0}\" in {1}: {2} [HTTP: {3}]".format(resp.url, filename, target, redir_status_code))
                        self.checked_remote_targets[resp.url] = resp.status_code
                        self.checked_remote_targets[target] = redir_status_code
                    else:
                        self.checked_remote_targets[target] = resp.status_code

                    if resp.status_code > 399:  # Error
                        self.logger.error("Broken link in {0}: {1} [Error {2}]".format(filename, target, resp.status_code))
                        continue
                    elif resp.status_code <= 399:  # The address leads *somewhere* that is not an error
                        self.logger.debug("Successfully checked remote link in {0}: {1} [HTTP: {2}]".format(filename, target, resp.status_code))
                        continue
                    self.logger.warn("Could not check remote link in {0}: {1} [Unknown problem]".format(filename, target))
                    continue

                if url_type == 'rel_path':
                    if target.startswith('/'):
                        target_filename = os.path.abspath(
                            os.path.join(self.site.config['OUTPUT_FOLDER'], unquote(target.lstrip('/'))))
                    else:  # Relative path
                        unquoted_target = unquote(target).encode('utf-8') if sys.version_info.major >= 3 else unquote(target).decode('utf-8')
                        target_filename = os.path.abspath(
                            os.path.join(os.path.dirname(filename).encode('utf-8'), unquoted_target))

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
                        self.logger.info("Good link {0} => {1}".format(target, target_filename))
                        self.existing_targets.add(target_filename)
                    else:
                        rv = True
                        self.logger.warn("Broken link in {0}: {1}".format(filename, target))
                        if find_sources:
                            self.logger.warn("Possible sources:")
                            self.logger.warn("\n".join(deps[filename]))
                            self.logger.warn("===============================\n")
        except Exception as exc:
            self.logger.error(u"Error with: {0} {1}".format(filename, exc))
        return rv

    def scan_links(self, find_sources=False, check_remote=False):
        """Check links on the site."""
        self.logger.debug("Checking Links:")
        self.logger.debug("===============\n")
        self.logger.debug("{0} mode".format(self.site.config['URL_TYPE']))
        failure = False
        # Maybe we should just examine all HTML files
        output_folder = self.site.config['OUTPUT_FOLDER']

        if urlparse(self.site.config['BASE_URL']).netloc == 'example.com':
            self.logger.error("You've not changed the SITE_URL (or BASE_URL) setting from \"example.com\"!")

        for fname in _call_nikola_list(self.site, self.cache)[0]:
            if fname.startswith(output_folder):
                if '.html' == fname[-5:]:
                    if self.analyze(fname, find_sources, check_remote):
                        failure = True
                if '.atom' == fname[-5:]:
                    if self.analyze(fname, find_sources, False):
                        failure = True
                if fname.endswith('sitemap.xml') or fname.endswith('sitemapindex.xml'):
                    if self.analyze(fname, find_sources, False):
                        failure = True
        if not failure:
            self.logger.debug("All links checked.")
        return failure

    def scan_files(self):
        """Check files in the site, find missing and orphaned files."""
        failure = False
        self.logger.debug("Checking Files:")
        self.logger.debug("===============\n")
        only_on_output, only_on_input = real_scan_files(self.site, self.cache)

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
            self.logger.debug("All files checked.")
        return failure

    def clean_files(self):
        """Remove orphaned files."""
        only_on_output, _ = real_scan_files(self.site, self.cache)
        for f in only_on_output:
            self.logger.debug('removed: {0}'.format(f))
            os.unlink(f)

        warn_flag = bool(only_on_output)

        # Find empty directories and remove them
        output_folder = self.site.config['OUTPUT_FOLDER']
        all_dirs = []
        for root, dirs, files in os.walk(output_folder, followlinks=True):
            all_dirs.append(root)
        all_dirs.sort(key=len, reverse=True)
        for d in all_dirs:
            try:
                os.rmdir(d)
                self.logger.debug('removed: {0}/'.format(d))
                warn_flag = True
            except OSError:
                pass

        if warn_flag:
            self.logger.warn('Some files or directories have been removed, your site may need rebuilding')

        return True
