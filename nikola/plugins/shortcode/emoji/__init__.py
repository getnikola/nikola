# -*- coding: utf-8 -*-
# This file is public domain according to its author, Roberto Alsina

"""Emoji directive for reStructuredText."""

import glob
import json
import os

from nikola.plugin_categories import ShortcodePlugin
from nikola import utils

TABLE = {}

LOGGER = utils.get_logger('scan_posts')


def _populate():
    for fname in glob.glob(os.path.join(os.path.dirname(__file__), 'data', '*.json')):
        with open(fname, encoding="utf-8-sig") as inf:
            data = json.load(inf)
            data = data[list(data.keys())[0]]
            data = data[list(data.keys())[0]]
            for item in data:
                if item['key'] in TABLE:
                    LOGGER.warning('Repeated emoji {}'.format(item['key']))
                else:
                    TABLE[item['key']] = item['value']


class Plugin(ShortcodePlugin):
    """Plugin for gist directive."""

    name = "emoji"

    def handler(self, name, filename=None, site=None, data=None, lang=None, post=None):
        """Create HTML for emoji."""
        if not TABLE:
            _populate()
        try:
            output = f'''<span class="emoji">{TABLE[name]}</span>'''
        except KeyError:
            LOGGER.warning(f'Unknown emoji {name}')
            output = f'''<span class="emoji error">{name}</span>'''

        return output, []
