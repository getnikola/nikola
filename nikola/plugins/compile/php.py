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

"""Page compiler plugin for PHP."""

from __future__ import unicode_literals

import os
import io

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, write_metadata
from hashlib import md5


class CompilePhp(PageCompiler):
    """Compile PHP into PHP."""

    name = "php"
    friendly_name = "PHP"

    def compile(self, source, dest, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        with io.open(dest, "w+", encoding="utf8") as out_file:
            with open(source, "rb") as in_file:
                hash = md5(in_file.read()).hexdigest()
                out_file.write('<!-- __NIKOLA_PHP_TEMPLATE_INJECTION source:{0} checksum:{1}__ -->'.format(source, hash))
        return True

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile PHP into HTML strings."""
        return data

    def create_post(self, path, **kw):
        """Create a new post."""
        content = kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        # is_page is not used by create_post as of now.
        kw.pop('is_page', False)
        metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)
        if not metadata['description']:
            # For PHP, a description must be set.  Otherwise, Nikola will
            # take the first 200 characters of the post as the Open Graph
            # description (og:description meta element)!
            # If the PHP source leaks there:
            # (a) The script will be executed multiple times
            # (b) PHP may encounter a syntax error if it cuts too early,
            #     therefore completely breaking the page
            # Here, we just use the title.  The user should come up with
            # something better, but just using the title does the job.
            metadata['description'] = metadata['title']
        makedirs(os.path.dirname(path))
        if not content.endswith('\n'):
            content += '\n'
        with io.open(path, "w+", encoding="utf8") as fd:
            if onefile:
                fd.write('<!--\n')
                fd.write(write_metadata(metadata))
                fd.write('-->\n\n')
            fd.write(content)

    def extension(self):
        """Return extension used for PHP files."""
        return ".php"
