# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

"""Page compiler plugin for pandoc.

You will need, of course, to install pandoc
"""


import io
import os
import subprocess
from typing import List
from pathlib import Path

from nikola.plugin_categories import PageCompiler
from nikola.utils import req_missing, makedirs, write_metadata


class CompilePandoc(PageCompiler):
    """Compile markups into HTML using pandoc."""

    name = "pandoc"
    friendly_name = "pandoc"

    def set_site(self, site):
        """Set Nikola site."""
        self.config_dependencies = [str(site.config['PANDOC_OPTIONS'])]
        super().set_site(site)

    def _get_pandoc_options(self, source: str) -> List[str]:
        """Obtain pandoc args from config depending on type and file extensions."""
        # Union[List[str], Dict[str, List[str]]]
        config_options = self.site.config['PANDOC_OPTIONS']
        if isinstance(config_options, (list, tuple)):
            pandoc_options = list(config_options)
        elif isinstance(config_options, dict):
            ext = Path(source).suffix
            try:
                pandoc_options = list(config_options[ext])
            except KeyError:
                self.logger.warning('Setting PANDOC_OPTIONS to [], because extension {} is not defined in PANDOC_OPTIONS: {}.'.format(ext, config_options))
                pandoc_options = []
        else:
            self.logger.warning('Setting PANDOC_OPTIONS to [], because PANDOC_OPTIONS is expected to be of type Union[List[str], Dict[str, List[str]]] but this is not: {}'.format(config_options))
            pandoc_options = []
        return pandoc_options

    def compile(self, source, dest, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        try:
            subprocess.check_call(['pandoc', '-o', dest, source] + self._get_pandoc_options(source))
            with open(dest, 'r', encoding='utf-8-sig') as inf:
                output, shortcode_deps = self.site.apply_shortcodes(inf.read())
            with open(dest, 'w', encoding='utf-8') as outf:
                outf.write(output)
            if post is None:
                if shortcode_deps:
                    self.logger.error(
                        "Cannot save dependencies for post {0} (post unknown)",
                        source)
            else:
                post._depfile[dest] += shortcode_deps
        except OSError as e:
            if e.strreror == 'No such file or directory':
                req_missing(['pandoc'], 'build this site (compile with pandoc)', python=False)

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile into HTML strings."""
        raise ValueError("Pandoc compiler does not support compile_string due to multiple output formats")

    def create_post(self, path, **kw):
        """Create a new post."""
        content = kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        # is_page is not used by create_post as of now.
        kw.pop('is_page', False)
        metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)
        makedirs(os.path.dirname(path))
        if not content.endswith('\n'):
            content += '\n'
        with io.open(path, "w+", encoding="utf8") as fd:
            if onefile:
                fd.write(write_metadata(metadata, comment_wrap=True, site=self.site, compiler=self))
            fd.write(content)
