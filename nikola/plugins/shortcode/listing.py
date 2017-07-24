# -*- coding: utf-8 -*-
# This file is public domain according to its author, Brian Hsu

"""Listing Shortcode"""

import os

import pygments

from nikola.plugin_categories import ShortcodePlugin

try:
    from urlparse import urlunsplit
except ImportError:
    from urllib.parse import urlunsplit  # NOQA


class Plugin(ShortcodePlugin):
    """Plugin for listing shortcode."""

    name = "listing"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
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
