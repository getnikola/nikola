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

"""Page compiler plugin for HTML source files."""

from __future__ import unicode_literals

import io
import os

import lxml.html

from nikola import shortcodes as sc
from nikola.plugin_categories import PageCompiler
from nikola.utils import LocaleBorg, makedirs, map_metadata, write_metadata


class CompileHtml(PageCompiler):
    """Compile HTML into HTML."""

    name = "html"
    friendly_name = "HTML"

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile HTML into HTML strings, with shortcode support."""
        if not is_two_file:
            _, data = self.split_metadata(data)
        new_data, shortcodes = sc.extract_shortcodes(data)
        return self.site.apply_shortcodes_uuid(new_data, shortcodes, filename=source_path, with_dependencies=True, extra_context=dict(post=post))

    def compile(self, source, dest, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        with io.open(dest, "w+", encoding="utf8") as out_file:
            with io.open(source, "r", encoding="utf8") as in_file:
                data = in_file.read()
            data, shortcode_deps = self.compile_string(data, source, is_two_file, post, lang)
            out_file.write(data)
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
        with io.open(path, "w+", encoding="utf8") as fd:
            if onefile:
                fd.write('<!--\n')
                fd.write(write_metadata(metadata))
                fd.write('-->\n\n')
            fd.write(content)

    def read_metadata(self, post, file_metadata_regexp=None, unslugify_titles=False, lang=None):
        """Read the metadata from a post's meta tags, and return a metadata dict."""
        if lang is None:
            lang = LocaleBorg().current_lang
        source_path = post.translated_source_path(lang)

        with io.open(source_path, 'r', encoding='utf-8') as inf:
            data = inf.read()

        metadata = {}
        doc = lxml.html.document_fromstring(data)
        title_tag = doc.find('*//title')
        if title_tag is not None:
            metadata['title'] = title_tag.text
        meta_tags = doc.findall('*//meta')
        for tag in meta_tags:
            k = tag.get('name').lower()
            if not k:
                continue
            elif k == 'keywords':
                k = 'tags'
            metadata[k] = tag.get('content', '')
        map_metadata(metadata, 'html_metadata', self.site.config)
        return metadata
