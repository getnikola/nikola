# -*- coding: utf-8 -*-
# Copyright (c) 2012 Roberto Alsina y otros.

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

from __future__ import unicode_literals, print_function

import codecs
import os

import lxml.html

from . import utils

__all__ = ['Post']


class Post(object):

    """Represents a blog post or web page."""

    def __init__(self, source_path, cache_folder, destination, use_in_feeds,
                 translations, default_lang, blog_url, messages, template_name,
                 file_metadata_regexp=None):
        """Initialize post.

        The base path is the .txt post file. From it we calculate
        the meta file, as well as any translations available, and
        the .html fragment file path.
        """
        self.translated_to = set([default_lang])
        self.prev_post = None
        self.next_post = None
        self.blog_url = blog_url
        self.is_draft = False
        self.is_mathjax = False
        self.source_path = source_path  # posts/blah.txt
        self.post_name = os.path.splitext(source_path)[0]  # posts/blah
        # cache/posts/blah.html
        self.base_path = os.path.join(cache_folder, self.post_name + ".html")
        self.metadata_path = self.post_name + ".meta"  # posts/blah.meta
        self.folder = destination
        self.translations = translations
        self.default_lang = default_lang
        self.messages = messages
        self.template_name = template_name
        if os.path.isfile(self.metadata_path):
            with codecs.open(self.metadata_path, "r", "utf8") as meta_file:
                meta_data = meta_file.readlines()
            while len(meta_data) < 6:
                meta_data.append("")
            (default_title, default_pagename, self.date, self.tags,
                self.link, default_description) = [x.strip() for x in
                                                   meta_data][:6]
        else:
            (default_title, default_pagename, self.date, self.tags,
                self.link, default_description) = utils.get_meta(
                    self.source_path, file_metadata_regexp)

        if not default_title or not default_pagename or not self.date:
            raise OSError("You must set a title and slug and date! [%s]" %
                          source_path)

        self.date = utils.to_datetime(self.date)
        self.tags = [x.strip() for x in self.tags.split(',')]
        self.tags = [_f for _f in self.tags if _f]

        # While draft comes from the tags, it's not really a tag
        self.use_in_feeds = use_in_feeds and "draft" not in self.tags
        self.is_draft = 'draft' in self.tags
        self.tags = [t for t in self.tags if t != 'draft']
        
        # If mathjax is a tag, then enable mathjax rendering support 
        self.is_mathjax = 'mathjax' in self.tags

        self.pagenames = {}
        self.titles = {}
        self.descriptions = {}
        # Load internationalized titles
        # TODO: this has gotten much too complicated. Rethink.
        for lang in translations:
            if lang == default_lang:
                self.titles[lang] = default_title
                self.pagenames[lang] = default_pagename
                self.descriptions[lang] = default_description
            else:
                metadata_path = self.metadata_path + "." + lang
                source_path = self.source_path + "." + lang
                if os.path.isfile(source_path):
                    self.translated_to.add(lang)
                try:
                    if os.path.isfile(metadata_path):
                        with codecs.open(
                                metadata_path, "r", "utf8") as meta_file:
                            meta_data = [x.strip() for x in
                                         meta_file.readlines()]
                            while len(meta_data) < 6:
                                meta_data.append("")
                            self.titles[lang] = meta_data[0] or default_title
                            self.pagenames[lang] = meta_data[1] or\
                                default_pagename
                            self.descriptions[lang] = meta_data[5] or\
                                default_description
                    else:
                        ttitle, ppagename, tmp1, tmp2, tmp3, ddescription = \
                            utils.get_meta(source_path, file_metadata_regexp)
                        self.titles[lang] = ttitle or default_title
                        self.pagenames[lang] = ppagename or default_pagename
                        self.descriptions[lang] = ddescription or\
                            default_description
                except:
                    self.titles[lang] = default_title
                    self.pagenames[lang] = default_pagename
                    self.descriptions[lang] = default_description

    def title(self, lang):
        """Return localized title."""
        return self.titles[lang]

    def description(self, lang):
        """Return localized description."""
        return self.descriptions[lang]

    def deps(self, lang):
        """Return a list of dependencies to build this post's page."""
        deps = [self.base_path]
        if lang != self.default_lang:
            deps += [self.base_path + "." + lang]
        deps += self.fragment_deps(lang)
        return deps

    def fragment_deps(self, lang):
        """Return a list of dependencies to build this post's fragment."""
        deps = [self.source_path]
        if os.path.isfile(self.metadata_path):
            deps.append(self.metadata_path)
        if lang != self.default_lang:
            lang_deps = list(filter(os.path.exists, [x + "." + lang for x in
                                                     deps]))
            deps += lang_deps
        return deps

    def is_translation_available(self, lang):
        """Return true if the translation actually exists."""
        return lang in self.translated_to

    def _translated_file_path(self, lang):
        """Return path to the translation's file, or to the original."""
        file_name = self.base_path
        if lang != self.default_lang:
            file_name_lang = file_name + ".%s" % lang
            if os.path.exists(file_name_lang):
                file_name = file_name_lang
        return file_name

    def text(self, lang, teaser_only=False, strip_html=False):
        """Read the post file for that language and return its contents"""
        file_name = self._translated_file_path(lang)

        with codecs.open(file_name, "r", "utf8") as post_file:
            data = post_file.read()

        if data:
            data = lxml.html.make_links_absolute(data, self.permalink())
        if data and teaser_only:
            e = lxml.html.fromstring(data)
            teaser = []
            flag = False
            for elem in e:
                elem_string = lxml.html.tostring(elem).decode('utf8')
                if '<!-- TEASER_END -->' in elem_string.upper():
                    flag = True
                    break
                teaser.append(elem_string)
            if flag:
                teaser.append('<p><a href="%s">%s...</a></p>' %
                              (self.permalink(lang),
                               self.messages[lang]["Read more"]))
            data = ''.join(teaser)

        if data and strip_html:
            content = lxml.html.fromstring(data)
            data = content.text_content().strip()  # No whitespace wanted.

        return data

    def destination_path(self, lang, extension='.html'):
        path = os.path.join(self.translations[lang],
                            self.folder, self.pagenames[lang] + extension)
        return path

    def permalink(self, lang=None, absolute=False, extension='.html'):
        if lang is None:
            lang = self.default_lang
        pieces = list(os.path.split(self.translations[lang]))
        pieces += list(os.path.split(self.folder))
        pieces += [self.pagenames[lang] + extension]
        pieces = [_f for _f in pieces if _f]
        if absolute:
            pieces = [self.blog_url] + pieces
        else:
            pieces = [""] + pieces
        link = "/".join(pieces)
        return link

    def source_ext(self):
        return os.path.splitext(self.source_path)[1]
