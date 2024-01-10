# -*- coding: utf-8 -*-

# Copyright © 2017-2024 Roberto Alsina and others.

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

"""Listing shortcode (equivalent to reST’s listing directive)."""

import os
from urllib.parse import urlunsplit

import pygments

from nikola.plugin_categories import ShortcodePlugin


class Plugin(ShortcodePlugin):
    """Plugin for listing shortcode."""

    name = "listing"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        Plugin.folders = site.config['LISTINGS_FOLDERS']
        return super().set_site(site)

    def handler(self, fname, language='text', linenumbers=False, filename=None, site=None, data=None, lang=None, post=None):
        """Create HTML for a listing."""
        fname = fname.replace('/', os.sep)
        if len(self.folders) == 1:
            listings_folder = next(iter(self.folders.keys()))
            if fname.startswith(listings_folder):
                fpath = os.path.join(fname)  # new syntax: specify folder name
            else:
                # old syntax: don't specify folder name
                fpath = os.path.join(listings_folder, fname)
        else:
            # must be new syntax: specify folder name
            fpath = os.path.join(fname)
        linenumbers = 'table' if linenumbers else False
        deps = [fpath]
        with open(fpath, 'r') as inf:
            target = urlunsplit(
                ("link", 'listing', fpath.replace('\\', '/'), '', ''))
            src_target = urlunsplit(
                ("link", 'listing_source', fpath.replace('\\', '/'), '', ''))
            src_label = self.site.MESSAGES('Source')

            data = inf.read()
            lexer = pygments.lexers.get_lexer_by_name(language)
            formatter = pygments.formatters.get_formatter_by_name(
                'html', linenos=linenumbers)
            output = '<a href="{1}">{0}</a>  <a href="{3}">({2})</a>' .format(
                fname, target, src_label, src_target) + pygments.highlight(data, lexer, formatter)

        return output, deps
