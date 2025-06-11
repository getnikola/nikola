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

"""Page compiler plugin for HTML source files."""


import os
from pathlib import Path

import lxml.html

from nikola import shortcodes as sc
from nikola.plugin_categories import PageCompiler
from nikola.utils import LocaleBorg, makedirs, map_metadata, write_metadata


class CompileHtml(PageCompiler):
    """Compile HTML into HTML."""

    name = "html"
    friendly_name = "HTML"
    supports_metadata = True

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile HTML into HTML strings, with shortcode support."""
        if not is_two_file:
            _, data = self.split_metadata(data, post, lang)
        new_data, shortcodes = sc.extract_shortcodes(data)
        return self.site.apply_shortcodes_uuid(new_data, shortcodes, filename=source_path, extra_context={'post': post})

    def compile(self, source, dest, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        data = Path(source).read_text(encoding="utf-8-sig")
        data, shortcode_deps = self.compile_string(data, source, is_two_file, post, lang)
        Path(dest).write_text(data, encoding="utf-8")
        if post is None:
            if shortcode_deps:
                self.logger.error(
                    "Cannot save dependencies for post {0} (post unknown)",
                    source)
        else:
            post._depfile[dest] += shortcode_deps
        return True

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

    def read_metadata(self, post, file_metadata_regexp=None, unslugify_titles=False, lang=None):
        """Read the metadata from a post's meta tags, and return a metadata dict."""
        if lang is None:
            lang = LocaleBorg().current_lang
        source_path = post.translated_source_path(lang)

        data = Path(source_path).read_text(encoding='utf-8-sig')

        metadata = {}
        try:
            doc = lxml.html.document_fromstring(data)
        except lxml.etree.ParserError as e:
            # Issue #374 -> #2851
            if str(e) == "Document is empty":
                return {}
            # let other errors raise
            raise
        title_tag = doc.find('*//title')
        if title_tag is not None and title_tag.text:
            metadata['title'] = title_tag.text
        meta_tags = doc.findall('*//meta')
        for tag in meta_tags:
            k = tag.get('name', '').lower()
            if not k:
                continue
            elif k == 'keywords':
                k = 'tags'
            content = tag.get('content')
            if content:
                metadata[k] = content
        map_metadata(metadata, 'html_metadata', self.site.config)
        return metadata
