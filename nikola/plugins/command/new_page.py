# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina, Chris Warrick and others.

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

"""Create a new page."""

from __future__ import unicode_literals, print_function

from nikola.plugin_categories import Command


class CommandNewPage(Command):
    """Create a new page."""

    name = "new_page"
    doc_usage = "[options] [path]"
    doc_purpose = "create a new page in the site"
    cmd_options = [
        {
            'name': 'title',
            'short': 't',
            'long': 'title',
            'type': str,
            'default': '',
            'help': 'Title for the page.'
        },
        {
            'name': 'author',
            'short': 'a',
            'long': 'author',
            'type': str,
            'default': '',
            'help': 'Author of the post.'
        },
        {
            'name': 'onefile',
            'short': '1',
            'type': bool,
            'default': False,
            'help': 'Create the page with embedded metadata (single file format)'
        },
        {
            'name': 'twofile',
            'short': '2',
            'type': bool,
            'default': False,
            'help': 'Create the page with separate metadata (two file format)'
        },
        {
            'name': 'edit',
            'short': 'e',
            'type': bool,
            'default': False,
            'help': 'Open the page (and meta file, if any) in $EDITOR after creation.'
        },
        {
            'name': 'content_format',
            'short': 'f',
            'long': 'format',
            'type': str,
            'default': '',
            'help': 'Markup format for the page (use --available-formats for list)',
        },
        {
            'name': 'available-formats',
            'short': 'F',
            'long': 'available-formats',
            'type': bool,
            'default': False,
            'help': 'List all available input formats'
        },
        {
            'name': 'import',
            'short': 'i',
            'long': 'import',
            'type': str,
            'default': '',
            'help': 'Import an existing file instead of creating a placeholder'
        },
    ]

    def _execute(self, options, args):
        """Create a new page."""
        # Defaults for some values that don’t apply to pages and the is_page option (duh!)
        options['tags'] = ''
        options['schedule'] = False
        options['is_page'] = True
        # Even though stuff was split into `new_page`, it’s easier to do it
        # there not to duplicate the code.
        p = self.site.plugin_manager.getPluginByName('new_post', 'Command').plugin_object
        return p.execute(options, args)
