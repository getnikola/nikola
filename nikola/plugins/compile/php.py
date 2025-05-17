# -*- coding: utf-8 -*-

# Copyright © 2012-2025 Roberto Alsina and others.

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

import os
from hashlib import md5
from pathlib import Path

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, write_metadata


class CompilePhp(PageCompiler):
    """Compile PHP into PHP."""

    name = "php"
    friendly_name = "PHP"

    def compile(self, source, dest, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        text = Path(source).read_bytes()
        hash = md5(text).hexdigest()
        out = f'<!-- __NIKOLA_PHP_TEMPLATE_INJECTION source:{source} checksum:{hash}__ -->'
        Path(dest).write_text(out, encoding="utf8")
        return True

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile PHP into HTML strings."""
        return data, []

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
        if onefile:
            content = write_metadata(metadata, comment_wrap=True, site=self.site, compiler=self) + content
        Path(path).write_text(content, encoding="utf8")

    def extension(self):
        """Return extension used for PHP files."""
        return ".php"
