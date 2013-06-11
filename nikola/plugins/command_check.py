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
import os
import re
import sys
try:
    from urllib import unquote
    from urlparse import urlparse
except ImportError:
    from urllib.parse import unquote, urlparse  # NOQA

import lxml.html

from nikola.plugin_categories import Command


class CommandCheck(Command):
    """Check the generated site."""

    name = "check"

    doc_usage = "-l [--find-sources] | -f"
    doc_purpose = "Check links and files in the generated site."
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
            'help': 'Check for unknown files',
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
    ]

    def _execute(self, options, args):
        """Check the generated site."""
        if not options['links'] and not options['files'] and not options['clean']:
            print(self.help())
            return False
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
        try:
            filename = task.split(":")[-1]
            d = lxml.html.fromstring(open(filename).read())
            for l in d.iterlinks():
                target = l[0].attrib[l[1]]
                if target == "#":
                    continue
                parsed = urlparse(target)
                if parsed.scheme or target.startswith('//'):
                    continue
                if parsed.fragment:
                    target = target.split('#')[0]
                target_filename = os.path.abspath(
                    os.path.join(os.path.dirname(filename), unquote(target)))
                if any(re.match(x, target_filename) for x in self.whitelist):
                    continue
                elif target_filename not in self.existing_targets:
                    if os.path.exists(target_filename):
                        self.existing_targets.add(target_filename)
                    else:
                        rv = True
                        print("Broken link in {0}: ".format(filename), target)
                        if find_sources:
                            print("Possible sources:")
                            print(os.popen('nikola list --deps ' + task, 'r').read())
                            print("===============================\n")
        except Exception as exc:
            print("Error with:", filename, exc)
        return rv

    def scan_links(self, find_sources=False):
        print("Checking Links:\n===============\n")
        failure = False
        for task in os.popen('nikola list --all', 'r').readlines():
            task = task.strip()
            if task.split(':')[0] in (
                    'render_tags', 'render_archive',
                    'render_galleries', 'render_indexes',
                    'render_pages'
                    'render_site') and '.html' in task:
                if self.analyze(task, find_sources):
                    failure = True
        return failure

    def scan_files(self):
        failure = False
        print("Checking Files:\n===============\n")
        only_on_output, only_on_input = self.real_scan_files()
        if only_on_output:
            only_on_output.sort()
            print("\nFiles from unknown origins:\n")
            for f in only_on_output:
                print(f)
            failure = True
        if only_on_input:
            only_on_input.sort()
            print("\nFiles not generated:\n")
            for f in only_on_input:
                print(f)
        return failure

    def clean_files(self):
        only_on_output, _ = self.real_scan_files()
        for f in only_on_output:
            os.unlink(f)
        return True

    def real_scan_files(self):
        task_fnames = set([])
        real_fnames = set([])
        output_folder = self.site.config['OUTPUT_FOLDER']
        # First check that all targets are generated in the right places
        for task in os.popen('nikola list --all', 'r').readlines():
            task = task.strip()
            if output_folder in task and ':' in task:
                fname = task.split(':', 1)[-1]
                task_fnames.add(fname)
        # And now check that there are no non-target files
        for root, dirs, files in os.walk(output_folder):
            for src_name in files:
                fname = os.path.join(root, src_name)
                real_fnames.add(fname)

        only_on_output = list(real_fnames - task_fnames)

        only_on_input = list(task_fnames - real_fnames)

        return (only_on_output, only_on_input)
