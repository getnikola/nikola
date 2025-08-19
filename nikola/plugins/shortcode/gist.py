# -*- coding: utf-8 -*-
# This file is public domain according to its author, Brian Hsu

"""Gist directive for reStructuredText."""

import requests

from nikola.plugin_categories import ShortcodePlugin


class Plugin(ShortcodePlugin):
    """Plugin for gist directive."""

    name = "gist"

    def get_raw_gist_with_filename(self, gistID, filename):
        """Get raw gist text for a filename."""
        url = '/'.join(("https://gist.github.com/raw", gistID, filename))
        return requests.get(url).text

    def get_raw_gist(self, gistID):
        """Get raw gist text."""
        url = f"https://gist.github.com/raw/{gistID}"
        try:
            return requests.get(url).text
        except requests.exceptions.RequestException:
            raise self.error(f'Cannot get gist for url={url}')

    def handler(self, gistID, filename=None, site=None, data=None, lang=None, post=None):
        """Create HTML for gist."""
        if 'https://' in gistID:
            gistID = gistID.split('/')[-1].strip()
        else:
            gistID = gistID.strip()
        embedHTML = ""
        rawGist = ""

        if filename is not None:
            rawGist = (self.get_raw_gist_with_filename(gistID, filename))
            embedHTML = (f'<script src="https://gist.github.com/{gistID}.js'
                         f'?file={filename}"></script>')
        else:
            rawGist = (self.get_raw_gist(gistID))
            embedHTML = (f'<script src="https://gist.github.com/{gistID}.js">'
                         '</script>')

        output = f'''{embedHTML}
        <noscript><pre>{rawGist}</pre></noscript>'''

        return output, []
