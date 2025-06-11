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

"""Page compiler plugin for Markdown."""

import json
import os
from pathlib import Path
import threading

from nikola import shortcodes as sc
from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing, write_metadata, LocaleBorg, map_metadata, NikolaPygmentsHTML

try:
    from markdown import Markdown
except ImportError:
    Markdown = None

# Override Pygments formatter for Markdown.
try:
    import markdown.extensions.codehilite
    markdown.extensions.codehilite.get_formatter_by_name = lambda _, **args: NikolaPygmentsHTML(**args)
except ImportError:
    pass


class ThreadLocalMarkdown(threading.local):
    """Convert Markdown to HTML using per-thread Markdown objects.

    See discussion in #2661.
    """

    def __init__(self, extensions, extension_configs):
        """Create a Markdown instance."""
        self.markdown = Markdown(extensions=extensions, extension_configs=extension_configs, output_format="html5")

    def convert(self, data):
        """Convert data to HTML and reset internal state."""
        result = self.markdown.convert(data)
        try:
            meta = {}
            for k in self.markdown.Meta:  # This reads everything as lists
                meta[k.lower()] = ','.join(self.markdown.Meta[k])
        except Exception:
            meta = {}
        self.markdown.reset()
        return result, meta


class CompileMarkdown(PageCompiler):
    """Compile Markdown into HTML."""

    name = "markdown"
    friendly_name = "Markdown"
    demote_headers = True
    site = None
    supports_metadata = False

    def set_site(self, site):
        """Set Nikola site."""
        super().set_site(site)
        self.config_dependencies = []
        extensions = []
        for plugin_info in self.get_compiler_extensions():
            self.config_dependencies.append(plugin_info.name)
            extensions.append(plugin_info.plugin_object)
            plugin_info.plugin_object.short_help = plugin_info.description

        site_extensions = self.site.config.get("MARKDOWN_EXTENSIONS")
        self.config_dependencies.append(str(sorted(site_extensions)))
        extensions.extend(site_extensions)

        site_extension_configs = self.site.config.get("MARKDOWN_EXTENSION_CONFIGS")
        if site_extension_configs:
            self.config_dependencies.append(json.dumps(site_extension_configs.values, sort_keys=True))

        if Markdown is not None:
            self.converters = {}
            for lang in self.site.config['TRANSLATIONS']:
                lang_extension_configs = site_extension_configs(lang) if site_extension_configs else {}
                self.converters[lang] = ThreadLocalMarkdown(extensions, lang_extension_configs)
        self.supports_metadata = 'markdown.extensions.meta' in extensions

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile Markdown into HTML strings."""
        if lang is None:
            lang = LocaleBorg().current_lang
        if Markdown is None:
            req_missing(['markdown'], 'build this site (compile Markdown)')
        if not is_two_file:
            _, data = self.split_metadata(data, post, lang)
        new_data, shortcodes = sc.extract_shortcodes(data)
        output, _ = self.converters[lang].convert(new_data)
        output, shortcode_deps = self.site.apply_shortcodes_uuid(output, shortcodes, filename=source_path, extra_context={'post': post})
        return output, shortcode_deps

    def compile(self, source, dest, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        if Markdown is None:
            req_missing(['markdown'], 'build this site (compile Markdown)')
        makedirs(os.path.dirname(dest))
        data = Path(source).read_text(encoding="utf-8-sig")
        output, shortcode_deps = self.compile_string(data, source, is_two_file, post, lang)
        Path(dest).write_text(output, encoding="utf-8")
        if post is None:
            if shortcode_deps:
                self.logger.error(
                    "Cannot save dependencies for post {0} (post unknown)",
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
        if onefile:
            content = write_metadata(metadata, comment_wrap=True, site=self.site, compiler=self) + content
        Path(path).write_text(content, encoding="utf-8")

    def read_metadata(self, post, lang=None):
        """Read the metadata from a post, and return a metadata dict."""
        lang = lang or self.site.config['DEFAULT_LANG']
        if not self.supports_metadata:
            return {}
        if Markdown is None:
            req_missing(['markdown'], 'build this site (compile Markdown)')
        if lang is None:
            lang = LocaleBorg().current_lang
        source = post.translated_source_path(lang)
        data = Path(source).read_text(encoding='utf-8-sig')
        # Note: markdown meta returns lowercase keys
        # If the metadata starts with "---" it's actually YAML and
        # we should not let markdown parse it, because it will do
        # bad things like setting empty tags to "''"
        if data.startswith('---\n'):
            return {}
        _, meta = self.converters[lang].convert(data)
        # Map metadata from other platforms to names Nikola expects (Issue #2817)
        map_metadata(meta, 'markdown_metadata', self.site.config)
        return meta
