# -*- coding: utf-8 -*-
# This file is public domain according to its author, Brian Hsu

"""Listing Shortcode"""

import os

import pygments

from nikola.plugin_categories import ShortcodePlugin


class Plugin(ShortcodePlugin):
    """Plugin for listing shortcode."""

    name = "listing"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        # Even though listings don't use CodeBlock anymore, I am
        # leaving these to make the code directive work with
        # docutils < 0.9
        Plugin.folders = site.config['LISTINGS_FOLDERS']
        return super(Plugin, self).set_site(site)

    def handler(self, fname, language='text', linenumbers=False, filename=None, site=None, data=None, lang=None, post=None):
        """Create HTML for a listing."""
        fname = fname.replace('/', os.sep)
        if len(self.folders) == 1:
            listings_folder = next(iter(self.folders.keys()))
            if fname.startswith(listings_folder):
                fpath = os.path.join(fname)  # new syntax: specify folder name
            else:
                fpath = os.path.join(listings_folder, fname)  # old syntax: don't specify folder name
        else:
            fpath = os.path.join(fname)  # must be new syntax: specify folder name
        linenumbers = 'table' if linenumbers else False
        deps = []
        with open(fpath, 'r') as inf:
            data = inf.read()
            lexer = pygments.lexers.get_lexer_by_name(language)
            formatter = pygments.formatters.get_formatter_by_name('html', linenos=linenumbers)
            output = pygments.highlight(data, lexer, formatter)

        return output, deps
