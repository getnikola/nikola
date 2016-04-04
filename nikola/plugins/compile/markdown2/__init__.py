# -*- coding: utf-8 -*-

"""Implementation of compile_html based on markdown."""

from __future__ import unicode_literals

import io
import os

try:
    from markdown2 import markdown
except ImportError:
    markdown = None  # NOQA
    nikola_extension = None

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing, write_metadata
from nikola.shortcodes import apply_shortcodes


class CompileMarkdown2(PageCompiler):
    """Compile Markdown into HTML."""

    name = "markdown2"
    friendly_name = "Markdown2"
    demote_headers = True
    extensions = {}
    site = None

    def set_site(self, site):
        """Set Nikola site."""
        super(CompileMarkdown2, self).set_site(site)
        self.config_dependencies = []
        for plugin_info in self.get_compiler_extensions():
            self.config_dependencies.append(plugin_info.name)
            self.extensions.append(plugin_info.plugin_object)
            plugin_info.plugin_object.short_help = plugin_info.description

        self.config_dependencies.append(str(sorted(site.config.get("MARKDOWN2_EXTENSIONS"))))

    def compile_html(self, source, dest, is_two_file=True):
        """Compile source file into HTML and save as dest."""
        if markdown is None:
            req_missing(['markdown'], 'build this site (compile Markdown2)')
        makedirs(os.path.dirname(dest))
        self.extensions = self.site.config.get("MARKDOWN2_EXTENSIONS")
        with io.open(dest, "w+", encoding="utf8") as out_file:
            with io.open(source, "r", encoding="utf8") as in_file:
                data = in_file.read()
            if not is_two_file:
                _, data = self.split_metadata(data)
            output = markdown(data, extras=self.extensions)
            output = apply_shortcodes(output, self.site.shortcode_registry, self.site, source)
            out_file.write(output)

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
