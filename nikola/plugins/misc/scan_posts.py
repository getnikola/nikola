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

"""The default post scanner."""

from __future__ import unicode_literals, print_function
import glob
import os
import sys

from nikola.plugin_categories import PostScanner
from nikola import utils
from nikola.post import Post

LOGGER = utils.get_logger('scan_posts', utils.STDERR_HANDLER)


class ScanPosts(PostScanner):
    """Scan posts in the site."""

    name = "scan_posts"

    def scan(self):
        """Create list of posts from POSTS and PAGES options."""
        seen = set([])
        if not self.site.quiet:
            print("Scanning posts", end='', file=sys.stderr)

        timeline = []

        for wildcard, destination, template_name, use_in_feeds in \
                self.site.config['post_pages']:
            if not self.site.quiet:
                print(".", end='', file=sys.stderr)
            destination_translatable = utils.TranslatableSetting('destination', destination, self.site.config['TRANSLATIONS'])
            dirname = os.path.dirname(wildcard)
            for dirpath, _, _ in os.walk(dirname, followlinks=True):
                rel_dest_dir = os.path.relpath(dirpath, dirname)
                # Get all the untranslated paths
                dir_glob = os.path.join(dirpath, os.path.basename(wildcard))  # posts/foo/*.rst
                untranslated = glob.glob(dir_glob)
                # And now get all the translated paths
                translated = set([])
                for lang in self.site.config['TRANSLATIONS'].keys():
                    if lang == self.site.config['DEFAULT_LANG']:
                        continue
                    lang_glob = utils.get_translation_candidate(self.site.config, dir_glob, lang)  # posts/foo/*.LANG.rst
                    translated = translated.union(set(glob.glob(lang_glob)))
                # untranslated globs like *.rst often match translated paths too, so remove them
                # and ensure x.rst is not in the translated set
                untranslated = set(untranslated) - translated

                # also remove from translated paths that are translations of
                # paths in untranslated_list, so x.es.rst is not in the untranslated set
                for p in untranslated:
                    translated = translated - set([utils.get_translation_candidate(self.site.config, p, l) for l in self.site.config['TRANSLATIONS'].keys()])

                full_list = list(translated) + list(untranslated)
                # We eliminate from the list the files inside any .ipynb folder
                full_list = [p for p in full_list
                             if not any([x.startswith('.')
                                         for x in p.split(os.sep)])]

                for base_path in full_list:
                    if base_path in seen:
                        continue
                    else:
                        seen.add(base_path)
                    try:
                        post = Post(
                            base_path,
                            self.site.config,
                            rel_dest_dir,
                            use_in_feeds,
                            self.site.MESSAGES,
                            template_name,
                            self.site.get_compiler(base_path),
                            destination_base=destination_translatable
                        )
                        timeline.append(post)
                    except Exception:
                        LOGGER.error('Error reading post {}'.format(base_path))
                        raise

        return timeline

    def supported_extensions(self):
        """Return a list of supported file extensions, or None if such a list isn't known beforehand."""
        return list({os.path.splitext(x[0])[1] for x in self.site.config['post_pages']})
