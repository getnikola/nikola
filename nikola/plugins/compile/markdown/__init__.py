# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Implementation of compile_html based on markdown."""

from __future__ import unicode_literals

import io
import os

try:
    from markdown import markdown
except ImportError:
    markdown = None  # NOQA
    nikola_extension = None
    gist_extension = None
    podcast_extension = None

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing, write_metadata


class CompileMarkdown(PageCompiler):
    """Compile Markdown into HTML."""

    name = "markdown"
    friendly_name = "Markdown"
    demote_headers = True
    extensions = []
    site = None

    def set_site(self, site):
        """Set Nikola site."""
        super(CompileMarkdown, self).set_site(site)
        self.config_dependencies = []
        for plugin_info in self.get_compiler_extensions():
            self.config_dependencies.append(plugin_info.name)
            self.extensions.append(plugin_info.plugin_object)
            plugin_info.plugin_object.short_help = plugin_info.description

        self.config_dependencies.append(str(sorted(site.config.get("MARKDOWN_EXTENSIONS"))))

    def compile_html(self, source, dest, is_two_file=True):
        """Compile source file into HTML and save as dest."""
        if markdown is None:
            req_missing(['markdown'], 'build this site (compile Markdown)')
        makedirs(os.path.dirname(dest))
        self.extensions += self.site.config.get("MARKDOWN_EXTENSIONS")
        try:
            post = self.site.post_per_input_file[source]
        except KeyError:
            post = None
        with io.open(dest, "w+", encoding="utf8") as out_file:
            with io.open(source, "r", encoding="utf8") as in_file:
                data = in_file.read()
            if not is_two_file:
                _, data = self.split_metadata(data)
            output = markdown(data, self.extensions, output_format="html5")
            output, shortcode_deps = self.site.apply_shortcodes(output, filename=source, with_dependencies=True, extra_context=dict(post=post))
            out_file.write(output)
        if post is None:
            if shortcode_deps:
                self.logger.error(
                    "Cannot save dependencies for post {0} due to unregistered source file name",
                    source)
        else:
            post._depfile[dest] += shortcode_deps

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
                fd.write('<!-- \n')
                fd.write(write_metadata(metadata))
                fd.write('-->\n\n')
            fd.write(content)
