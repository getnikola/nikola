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

"""The Post class."""

from __future__ import unicode_literals, print_function, absolute_import

import io
from collections import defaultdict
import datetime
import hashlib
import json
import os
import re
import string
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA

from . import utils

from blinker import signal
import dateutil.tz
import lxml.html
import natsort
try:
    import pyphen
except ImportError:
    pyphen = None

from math import ceil  # for reading time feature

# for tearDown with _reload we cannot use 'from import' to get forLocaleBorg
import nikola.utils
from .utils import (
    current_time,
    Functionary,
    LOGGER,
    LocaleBorg,
    slugify,
    to_datetime,
    unicode_str,
    demote_headers,
    get_translation_candidate,
    unslugify,
)
from .rc4 import rc4

__all__ = ('Post',)

TEASER_REGEXP = re.compile('<!--\s*TEASER_END(:(.+))?\s*-->', re.IGNORECASE)
_UPGRADE_METADATA_ADVERTISED = False


class Post(object):
    """Represent a blog post or site page."""

    def __init__(
        self,
        source_path,
        config,
        destination,
        use_in_feeds,
        messages,
        template_name,
        compiler
    ):
        """Initialize post.

        The source path is the user created post file. From it we calculate
        the meta file, as well as any translations available, and
        the .html fragment file path.
        """
        self.config = config
        self.compiler = compiler
        self.compile_html = self.compiler.compile_html
        self.demote_headers = self.compiler.demote_headers and self.config['DEMOTE_HEADERS']
        tzinfo = self.config['__tzinfo__']
        if self.config['FUTURE_IS_NOW']:
            self.current_time = None
        else:
            self.current_time = current_time(tzinfo)
        self.translated_to = set([])
        self._prev_post = None
        self._next_post = None
        self.base_url = self.config['BASE_URL']
        self.is_draft = False
        self.is_private = False
        self.strip_indexes = self.config['STRIP_INDEXES']
        self.index_file = self.config['INDEX_FILE']
        self.pretty_urls = self.config['PRETTY_URLS']
        self.source_path = source_path  # posts/blah.txt
        self.post_name = os.path.splitext(source_path)[0]  # posts/blah
        # cache[\/]posts[\/]blah.html
        self.base_path = os.path.join(self.config['CACHE_FOLDER'], self.post_name + ".html")
        # cache/posts/blah.html
        self._base_path = self.base_path.replace('\\', '/')
        self.metadata_path = self.post_name + ".meta"  # posts/blah.meta
        self.folder = destination
        self.translations = self.config['TRANSLATIONS']
        self.default_lang = self.config['DEFAULT_LANG']
        self.messages = messages
        self.skip_untranslated = not self.config['SHOW_UNTRANSLATED_POSTS']
        self._template_name = template_name
        self.is_two_file = True
        self.newstylemeta = True
        self._reading_time = None
        self._remaining_reading_time = None
        self._paragraph_count = None
        self._remaining_paragraph_count = None
        self._dependency_file_fragment = defaultdict(list)
        self._dependency_file_page = defaultdict(list)
        self._dependency_uptodate_fragment = defaultdict(list)
        self._dependency_uptodate_page = defaultdict(list)
        self._depfile = defaultdict(list)

        default_metadata, self.newstylemeta = get_meta(self, self.config['FILE_METADATA_REGEXP'], self.config['UNSLUGIFY_TITLES'])

        self.meta = Functionary(lambda: None, self.default_lang)
        self.meta[self.default_lang] = default_metadata

        # Load internationalized metadata
        for lang in self.translations:
            if os.path.isfile(get_translation_candidate(self.config, self.source_path, lang)):
                self.translated_to.add(lang)
            if lang != self.default_lang:
                meta = defaultdict(lambda: '')
                meta.update(default_metadata)
                _meta, _nsm = get_meta(self, self.config['FILE_METADATA_REGEXP'], self.config['UNSLUGIFY_TITLES'], lang)
                self.newstylemeta = self.newstylemeta and _nsm
                meta.update(_meta)
                self.meta[lang] = meta

        if not self.is_translation_available(self.default_lang):
            # Special case! (Issue #373)
            # Fill default_metadata with stuff from the other languages
            for lang in sorted(self.translated_to):
                default_metadata.update(self.meta[lang])

        # Load data field from metadata
        self.data = Functionary(lambda: None, self.default_lang)
        for lang in self.translations:
            if self.meta[lang].get('data') is not None:
                self.data[lang] = utils.load_data(self.meta[lang]['data'])

        if 'date' not in default_metadata and not use_in_feeds:
            # For pages we don't *really* need a date
            if self.config['__invariant__']:
                default_metadata['date'] = datetime.datetime(2013, 12, 31, 23, 59, 59, tzinfo=tzinfo)
            else:
                default_metadata['date'] = datetime.datetime.utcfromtimestamp(
                    os.stat(self.source_path).st_ctime).replace(tzinfo=dateutil.tz.tzutc()).astimezone(tzinfo)

        # If time zone is set, build localized datetime.
        try:
            self.date = to_datetime(self.meta[self.default_lang]['date'], tzinfo)
        except ValueError:
            raise ValueError("Invalid date '{0}' in file {1}".format(self.meta[self.default_lang]['date'], source_path))

        if 'updated' not in default_metadata:
            default_metadata['updated'] = default_metadata.get('date', None)

        self.updated = to_datetime(default_metadata['updated'])

        if 'title' not in default_metadata or 'slug' not in default_metadata \
                or 'date' not in default_metadata:
            raise ValueError("You must set a title (found '{0}'), a slug (found '{1}') and a date (found '{2}')! "
                             "[in file {3}]".format(default_metadata.get('title', None),
                                                    default_metadata.get('slug', None),
                                                    default_metadata.get('date', None),
                                                    source_path))

        if 'type' not in default_metadata:
            # default value is 'text'
            default_metadata['type'] = 'text'

        self.publish_later = False if self.current_time is None else self.date >= self.current_time

        is_draft = False
        is_private = False
        self._tags = {}
        for lang in self.translated_to:
            self._tags[lang] = natsort.natsorted(
                list(set([x.strip() for x in self.meta[lang]['tags'].split(',')])),
                alg=natsort.ns.F | natsort.ns.IC)
            self._tags[lang] = [t for t in self._tags[lang] if t]
            if 'draft' in [_.lower() for _ in self._tags[lang]]:
                is_draft = True
                LOGGER.debug('The post "{0}" is a draft.'.format(self.source_path))
                self._tags[lang].remove('draft')

            # TODO: remove in v8
            if 'retired' in self._tags[lang]:
                is_private = True
                LOGGER.warning('The "retired" tag in post "{0}" is now deprecated and will be removed in v8.  Use "private" instead.'.format(self.source_path))
                self._tags[lang].remove('retired')
            # end remove in v8

            if 'private' in self._tags[lang]:
                is_private = True
                LOGGER.debug('The post "{0}" is private.'.format(self.source_path))
                self._tags[lang].remove('private')

        # While draft comes from the tags, it's not really a tag
        self.is_draft = is_draft
        self.is_private = is_private
        self.is_post = use_in_feeds
        self.use_in_feeds = use_in_feeds and not is_draft and not is_private \
            and not self.publish_later

        # Register potential extra dependencies
        self.compiler.register_extra_dependencies(self)

    def _get_hyphenate(self):
        return bool(self.config['HYPHENATE'] or self.meta('hyphenate'))

    hyphenate = property(_get_hyphenate)

    def __repr__(self):
        """Provide a representation of the post object."""
        # Calculate a hash that represents most data about the post
        m = hashlib.md5()
        # source_path modification date (to avoid reading it)
        m.update(utils.unicode_str(os.stat(self.source_path).st_mtime).encode('utf-8'))
        clean_meta = {}
        for k, v in self.meta.items():
            sub_meta = {}
            clean_meta[k] = sub_meta
            for kk, vv in v.items():
                if vv:
                    sub_meta[kk] = vv
        m.update(utils.unicode_str(json.dumps(clean_meta, cls=utils.CustomEncoder, sort_keys=True)).encode('utf-8'))
        return '<Post: {0!r} {1}>'.format(self.source_path, m.hexdigest())

    def _has_pretty_url(self, lang):
        if self.pretty_urls and \
                self.meta[lang].get('pretty_url', '') != 'False' and \
                self.meta[lang]['slug'] != 'index':
            return True
        else:
            return False

    @property
    def is_mathjax(self):
        """True if this post has the mathjax tag in the current language or is a python notebook."""
        if self.compiler.name == 'ipynb':
            return True
        lang = nikola.utils.LocaleBorg().current_lang
        if self.is_translation_available(lang):
            return 'mathjax' in self.tags_for_language(lang)
        # If it has math in ANY other language, enable it. Better inefficient than broken.
        return 'mathjax' in self.alltags

    @property
    def alltags(self):
        """Return ALL the tags for this post."""
        tags = []
        for l in self._tags:
            tags.extend(self._tags[l])
        return list(set(tags))

    def tags_for_language(self, lang):
        """Return tags for a given language."""
        if lang in self._tags:
            return self._tags[lang]
        elif lang not in self.translated_to and self.skip_untranslated:
            return []
        elif self.default_lang in self._tags:
            return self._tags[self.default_lang]
        else:
            return []

    @property
    def tags(self):
        """Return tags for the current language."""
        lang = nikola.utils.LocaleBorg().current_lang
        return self.tags_for_language(lang)

    @property
    def prev_post(self):
        """Return previous post."""
        lang = nikola.utils.LocaleBorg().current_lang
        rv = self._prev_post
        while self.skip_untranslated:
            if rv is None:
                break
            if rv.is_translation_available(lang):
                break
            rv = rv._prev_post
        return rv

    @prev_post.setter  # NOQA
    def prev_post(self, v):
        """Set previous post."""
        self._prev_post = v

    @property
    def next_post(self):
        """Return next post."""
        lang = nikola.utils.LocaleBorg().current_lang
        rv = self._next_post
        while self.skip_untranslated:
            if rv is None:
                break
            if rv.is_translation_available(lang):
                break
            rv = rv._next_post
        return rv

    @next_post.setter  # NOQA
    def next_post(self, v):
        """Set next post."""
        self._next_post = v

    @property
    def template_name(self):
        """Return template name for this post."""
        lang = nikola.utils.LocaleBorg().current_lang
        return self.meta[lang]['template'] or self._template_name

    def formatted_date(self, date_format, date=None):
        """Return the formatted date as unicode."""
        return utils.LocaleBorg().formatted_date(date_format, date if date else self.date)

    def formatted_updated(self, date_format):
        """Return the updated date as unicode."""
        return self.formatted_date(date_format, self.updated)

    def title(self, lang=None):
        """Return localized title.

        If lang is not specified, it defaults to the current language from
        templates, as set in LocaleBorg.
        """
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang
        return self.meta[lang]['title']

    def author(self, lang=None):
        """Return localized author or BLOG_AUTHOR if unspecified.

        If lang is not specified, it defaults to the current language from
        templates, as set in LocaleBorg.
        """
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang
        if self.meta[lang]['author']:
            author = self.meta[lang]['author']
        else:
            author = self.config['BLOG_AUTHOR'](lang)

        return author

    def description(self, lang=None):
        """Return localized description."""
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang
        return self.meta[lang]['description']

    def add_dependency(self, dependency, add='both', lang=None):
        """Add a file dependency for tasks using that post.

        The ``dependency`` should be a string specifying a path, or a callable
        which returns such a string or a list of strings.

        The ``add`` parameter can be 'both', 'fragment' or 'page', to indicate
        that this dependency shall be used
         * when rendering the fragment to HTML ('fragment' and 'both'), or
         * when creating a page with parts of the ``Post`` embedded, which
           includes the HTML resulting from compiling the fragment ('page' or
           'both').

        If ``lang`` is not specified, this dependency is added for all languages.
        """
        if add not in {'fragment', 'page', 'both'}:
            raise Exception("Add parameter is '{0}', but must be either 'fragment', 'page', or 'both'.".format(add))
        if add == 'fragment' or add == 'both':
            self._dependency_file_fragment[lang].append((type(dependency) != str, dependency))
        if add == 'page' or add == 'both':
            self._dependency_file_page[lang].append((type(dependency) != str, dependency))

    def add_dependency_uptodate(self, dependency, is_callable=False, add='both', lang=None):
        """Add a dependency for task's ``uptodate`` for tasks using that post.

        This can be for example an ``utils.config_changed`` object, or a list of
        such objects.

        The ``is_callable`` parameter specifies whether ``dependency`` is a
        callable which generates an entry or a list of entries for the ``uptodate``
        list, or whether it is an entry which can directly be added (as a single
        object or a list of objects).

        The ``add`` parameter can be 'both', 'fragment' or 'page', to indicate
        that this dependency shall be used
         * when rendering the fragment to HTML ('fragment' and 'both'), or
         * when creating a page with parts of the ``Post`` embedded, which
           includes the HTML resulting from compiling the fragment ('page' or
           'both').

        If ``lang`` is not specified, this dependency is added for all languages.

        Example:

        post.add_dependency_uptodate(
            utils.config_changed({1: some_data}, 'uniqueid'), False, 'page')
        """
        if add == 'fragment' or add == 'both':
            self._dependency_uptodate_fragment[lang].append((is_callable, dependency))
        if add == 'page' or add == 'both':
            self._dependency_uptodate_page[lang].append((is_callable, dependency))

    def register_depfile(self, dep, dest=None, lang=None):
        """Register a dependency in the dependency file."""
        if not dest:
            dest = self.translated_base_path(lang)
        self._depfile[dest].append(dep)

    @staticmethod
    def write_depfile(dest, deps_list):
        """Write a depfile for a given language."""
        deps_path = dest + '.dep'
        if deps_list:
            deps_list = [p for p in deps_list if p != dest]  # Don't depend on yourself (#1671)
            with io.open(deps_path, "w+", encoding="utf8") as deps_file:
                deps_file.write('\n'.join(deps_list))
        else:
            if os.path.isfile(deps_path):
                os.unlink(deps_path)

    def _get_dependencies(self, deps_list):
        deps = []
        for dep in deps_list:
            if dep[0]:
                # callable
                result = dep[1]()
            else:
                # can add directly
                result = dep[1]
            # if result is a list, add its contents
            if type(result) == list:
                deps.extend(result)
            else:
                deps.append(result)
        return deps

    def deps(self, lang):
        """Return a list of file dependencies to build this post's page."""
        deps = []
        if self.default_lang in self.translated_to:
            deps.append(self.base_path)
            deps.append(self.source_path)
            if os.path.exists(self.metadata_path):
                deps.append(self.metadata_path)
        if lang != self.default_lang:
            cand_1 = get_translation_candidate(self.config, self.source_path, lang)
            cand_2 = get_translation_candidate(self.config, self.base_path, lang)
            if os.path.exists(cand_1):
                deps.extend([cand_1, cand_2])
            cand_3 = get_translation_candidate(self.config, self.metadata_path, lang)
            if os.path.exists(cand_3):
                deps.append(cand_3)
        if self.meta('data', lang):
            deps.append(self.meta('data', lang))
        deps += self._get_dependencies(self._dependency_file_page[lang])
        deps += self._get_dependencies(self._dependency_file_page[None])
        return sorted(deps)

    def deps_uptodate(self, lang):
        """Return a list of uptodate dependencies to build this post's page.

        These dependencies should be included in ``uptodate`` for the task
        which generates the page.
        """
        deps = []
        deps += self._get_dependencies(self._dependency_uptodate_page[lang])
        deps += self._get_dependencies(self._dependency_uptodate_page[None])
        deps.append(utils.config_changed({1: sorted(self.compiler.config_dependencies)}, 'nikola.post.Post.deps_uptodate:compiler:' + self.source_path))
        return deps

    def compile(self, lang):
        """Generate the cache/ file with the compiled post."""
        def wrap_encrypt(path, password):
            """Wrap a post with encryption."""
            with io.open(path, 'r+', encoding='utf8') as inf:
                data = inf.read() + "<!--tail-->"
            data = CRYPT.substitute(data=rc4(password, data))
            with io.open(path, 'w+', encoding='utf8') as outf:
                outf.write(data)

        dest = self.translated_base_path(lang)
        if not self.is_translation_available(lang) and not self.config['SHOW_UNTRANSLATED_POSTS']:
            return
        # Set the language to the right thing
        LocaleBorg().set_locale(lang)
        self.compile_html(
            self.translated_source_path(lang),
            dest,
            self.is_two_file)
        Post.write_depfile(dest, self._depfile[dest])

        signal('compiled').send({
            'source': self.translated_source_path(lang),
            'dest': dest,
            'post': self,
        })

        if self.meta('password'):
            # TODO: get rid of this feature one day (v8?; warning added in v7.3.0.)
            LOGGER.warn("The post {0} is using the `password` attribute, which may stop working in the future.")
            LOGGER.warn("Please consider switching to a more secure method of encryption.")
            LOGGER.warn("More details: https://github.com/getnikola/nikola/issues/1547")
            wrap_encrypt(dest, self.meta('password'))
        if self.publish_later:
            LOGGER.notice('{0} is scheduled to be published in the future ({1})'.format(
                self.source_path, self.date))

    def fragment_deps(self, lang):
        """Return a list of uptodate dependencies to build this post's fragment.

        These dependencies should be included in ``uptodate`` for the task
        which generates the fragment.
        """
        deps = []
        if self.default_lang in self.translated_to:
            deps.append(self.source_path)
        if os.path.isfile(self.metadata_path):
            deps.append(self.metadata_path)
        lang_deps = []
        if lang != self.default_lang:
            lang_deps = [get_translation_candidate(self.config, d, lang) for d in deps]
            deps += lang_deps
        deps = [d for d in deps if os.path.exists(d)]
        deps += self._get_dependencies(self._dependency_file_fragment[lang])
        deps += self._get_dependencies(self._dependency_file_fragment[None])
        return sorted(deps)

    def fragment_deps_uptodate(self, lang):
        """Return a list of file dependencies to build this post's fragment."""
        deps = []
        deps += self._get_dependencies(self._dependency_uptodate_fragment[lang])
        deps += self._get_dependencies(self._dependency_uptodate_fragment[None])
        deps.append(utils.config_changed({1: sorted(self.compiler.config_dependencies)}, 'nikola.post.Post.deps_uptodate:compiler:' + self.source_path))
        return deps

    def is_translation_available(self, lang):
        """Return True if the translation actually exists."""
        return lang in self.translated_to

    def translated_source_path(self, lang):
        """Return path to the translation's source file."""
        if lang in self.translated_to:
            if lang == self.default_lang:
                return self.source_path
            else:
                return get_translation_candidate(self.config, self.source_path, lang)
        elif lang != self.default_lang:
            return self.source_path
        else:
            return get_translation_candidate(self.config, self.source_path, sorted(self.translated_to)[0])

    def translated_base_path(self, lang):
        """Return path to the translation's base_path file."""
        return get_translation_candidate(self.config, self.base_path, lang)

    def _translated_file_path(self, lang):
        """Return path to the translation's file, or to the original."""
        if lang in self.translated_to:
            if lang == self.default_lang:
                return self.base_path
            else:
                return get_translation_candidate(self.config, self.base_path, lang)
        elif lang != self.default_lang:
            return self.base_path
        else:
            return get_translation_candidate(self.config, self.base_path, sorted(self.translated_to)[0])

    def text(self, lang=None, teaser_only=False, strip_html=False, show_read_more_link=True,
             feed_read_more_link=False, feed_links_append_query=None):
        """Read the post file for that language and return its contents.

        teaser_only=True breaks at the teaser marker and returns only the teaser.
        strip_html=True removes HTML tags
        show_read_more_link=False does not add the Read more... link
        feed_read_more_link=True uses FEED_READ_MORE_LINK instead of INDEX_READ_MORE_LINK
        lang=None uses the last used to set locale

        All links in the returned HTML will be relative.
        The HTML returned is a bare fragment, not a full document.
        """
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang
        file_name = self._translated_file_path(lang)

        # Yes, we compile it and screw it.
        # This may be controversial, but the user (or someone) is asking for the post text
        # and the post should not just refuse to give it.
        if not os.path.isfile(file_name):
            self.compile(lang)

        with io.open(file_name, "r", encoding="utf8") as post_file:
            data = post_file.read().strip()

        if self.compiler.extension() == '.php':
            return data
        try:
            document = lxml.html.fragment_fromstring(data, "body")
        except lxml.etree.ParserError as e:
            # if we don't catch this, it breaks later (Issue #374)
            if str(e) == "Document is empty":
                return ""
            # let other errors raise
            raise(e)
        base_url = self.permalink(lang=lang)
        document.make_links_absolute(base_url)

        if self.hyphenate:
            hyphenate(document, lang)

        try:
            data = lxml.html.tostring(document.body, encoding='unicode')
        except:
            data = lxml.html.tostring(document, encoding='unicode')

        if teaser_only:
            teaser_regexp = self.config.get('TEASER_REGEXP', TEASER_REGEXP)
            teaser = teaser_regexp.split(data)[0]
            if teaser != data:
                if not strip_html and show_read_more_link:
                    if teaser_regexp.search(data).groups()[-1]:
                        teaser_text = teaser_regexp.search(data).groups()[-1]
                    else:
                        teaser_text = self.messages[lang]["Read more"]
                    l = self.config['FEED_READ_MORE_LINK'](lang) if feed_read_more_link else self.config['INDEX_READ_MORE_LINK'](lang)
                    teaser += l.format(
                        link=self.permalink(lang, query=feed_links_append_query),
                        read_more=teaser_text,
                        min_remaining_read=self.messages[lang]["%d min remaining to read"] % (self.remaining_reading_time),
                        reading_time=self.reading_time,
                        remaining_reading_time=self.remaining_reading_time,
                        paragraph_count=self.paragraph_count,
                        remaining_paragraph_count=self.remaining_paragraph_count)
                # This closes all open tags and sanitizes the broken HTML
                document = lxml.html.fromstring(teaser)
                try:
                    data = lxml.html.tostring(document.body, encoding='unicode')
                except IndexError:
                    data = lxml.html.tostring(document, encoding='unicode')

        if data and strip_html:
            try:
                # Not all posts have a body. For example, you may have a page statically defined in the template that does not take content as input.
                content = lxml.html.fromstring(data)
                data = content.text_content().strip()  # No whitespace wanted.
            except lxml.etree.ParserError:
                data = ""
        elif data:
            if self.demote_headers:
                # see above
                try:
                    document = lxml.html.fromstring(data)
                    demote_headers(document, self.demote_headers)
                    data = lxml.html.tostring(document.body, encoding='unicode')
                except (lxml.etree.ParserError, IndexError):
                    data = lxml.html.tostring(document, encoding='unicode')

        return data

    @property
    def reading_time(self):
        """Reading time based on length of text."""
        if self._reading_time is None:
            text = self.text(strip_html=True)
            words_per_minute = 220
            words = len(text.split())
            markup = lxml.html.fromstring(self.text(strip_html=False))
            embeddables = [".//img", ".//picture", ".//video", ".//audio", ".//object", ".//iframe"]
            media_time = 0
            for embedded in embeddables:
                media_time += (len(markup.findall(embedded)) * 0.33)  # +20 seconds
            self._reading_time = int(ceil((words / words_per_minute) + media_time)) or 1
        return self._reading_time

    @property
    def remaining_reading_time(self):
        """Remaining reading time based on length of text (does not include teaser)."""
        if self._remaining_reading_time is None:
            text = self.text(teaser_only=True, strip_html=True)
            words_per_minute = 220
            words = len(text.split())
            self._remaining_reading_time = self.reading_time - int(ceil(words / words_per_minute)) or 1
        return self._remaining_reading_time

    @property
    def paragraph_count(self):
        """Return the paragraph count for this post."""
        if self._paragraph_count is None:
            # duplicated with Post.text()
            lang = nikola.utils.LocaleBorg().current_lang
            file_name = self._translated_file_path(lang)
            with io.open(file_name, "r", encoding="utf8") as post_file:
                data = post_file.read().strip()
            try:
                document = lxml.html.fragment_fromstring(data, "body")
            except lxml.etree.ParserError as e:
                # if we don't catch this, it breaks later (Issue #374)
                if str(e) == "Document is empty":
                    return ""
                # let other errors raise
                raise(e)

            # output is a float, for no real reason at all
            self._paragraph_count = int(document.xpath('count(//p)'))
        return self._paragraph_count

    @property
    def remaining_paragraph_count(self):
        """Return the remaining paragraph count for this post (does not include teaser)."""
        if self._remaining_paragraph_count is None:
            try:
                # Just asking self.text() is easier here.
                document = lxml.html.fragment_fromstring(self.text(teaser_only=True, show_read_more_link=False), "body")
            except lxml.etree.ParserError as e:
                # if we don't catch this, it breaks later (Issue #374)
                if str(e) == "Document is empty":
                    return ""
                # let other errors raise
                raise(e)

            self._remaining_paragraph_count = self.paragraph_count - int(document.xpath('count(//p)'))
        return self._remaining_paragraph_count

    def source_link(self, lang=None):
        """Return absolute link to the post's source."""
        ext = self.source_ext(True)
        link = "/" + self.destination_path(lang=lang, extension=ext, sep='/')
        link = utils.encodelink(link)
        return link

    def destination_path(self, lang=None, extension='.html', sep=os.sep):
        """Destination path for this post, relative to output/.

        If lang is not specified, it's the current language.
        Extension is used in the path if specified.
        """
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang
        if self._has_pretty_url(lang):
            path = os.path.join(self.translations[lang],
                                self.folder, self.meta[lang]['slug'], 'index' + extension)
        else:
            path = os.path.join(self.translations[lang],
                                self.folder, self.meta[lang]['slug'] + extension)
        if sep != os.sep:
            path = path.replace(os.sep, sep)
        if path.startswith('./'):
            path = path[2:]
        return path

    def section_color(self, lang=None):
        """Return the color of the post's section."""
        slug = self.section_slug(lang)
        if slug in self.config['POSTS_SECTION_COLORS'](lang):
            return self.config['POSTS_SECTION_COLORS'](lang)[slug]
        base = self.config['THEME_COLOR']
        return utils.colorize_str_from_base_color(slug, base)

    def section_link(self, lang=None):
        """Return the link to the post's section (deprecated)."""
        utils.LOGGER.warning("Post.section_link is deprecated. Please use " +
                             "site.link('section_index', post.section_slug()) instead.")
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang

        slug = self.section_slug(lang)
        t = os.path.normpath(self.translations[lang])
        if t == '.':
            t = ''
        link = '/' + '/'.join(i for i in (t, slug) if i) + '/'
        if not self.pretty_urls:
            link = urljoin(link, self.index_file)
        link = utils.encodelink(link)
        return link

    def section_name(self, lang=None):
        """Return the name of the post's section."""
        slug = self.section_slug(lang)
        if slug in self.config['POSTS_SECTION_NAME'](lang):
            name = self.config['POSTS_SECTION_NAME'](lang)[slug]
        else:
            name = slug.replace('-', ' ').title()
        return name

    def section_slug(self, lang=None):
        """Return the slug for the post's section."""
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang

        if not self.config['POSTS_SECTION_FROM_META']:
            dest = self.destination_path(lang)
            if dest[-(1 + len(self.index_file)):] == os.sep + self.index_file:
                dest = dest[:-(1 + len(self.index_file))]
            dirname = os.path.dirname(dest)
            slug = dest.split(os.sep)
            if not slug or dirname == '.':
                slug = self.messages[lang]["Uncategorized"]
            elif lang == slug[0]:
                slug = slug[1]
            else:
                slug = slug[0]
        else:
            slug = self.meta[lang]['section'].split(',')[0] if 'section' in self.meta[lang] else self.messages[lang]["Uncategorized"]
        return utils.slugify(slug, lang)

    def permalink(self, lang=None, absolute=False, extension='.html', query=None):
        """Return permalink for a post."""
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang

        # Let compilers override extension (e.g. the php compiler)
        if self.compiler.extension() != '.html':
            extension = self.compiler.extension()

        pieces = self.translations[lang].split(os.sep)
        pieces += self.folder.split(os.sep)
        if self._has_pretty_url(lang):
            pieces += [self.meta[lang]['slug'], 'index' + extension]
        else:
            pieces += [self.meta[lang]['slug'] + extension]
        pieces = [_f for _f in pieces if _f and _f != '.']
        link = '/' + '/'.join(pieces)
        if absolute:
            link = urljoin(self.base_url, link[1:])
        index_len = len(self.index_file)
        if self.strip_indexes and link[-(1 + index_len):] == '/' + self.index_file:
            link = link[:-index_len]
        if query:
            link = link + "?" + query
        link = utils.encodelink(link)
        return link

    @property
    def previewimage(self, lang=None):
        """Return the previewimage path."""
        if lang is None:
            lang = nikola.utils.LocaleBorg().current_lang

        image_path = self.meta[lang]['previewimage']

        if not image_path:
            return None

        # This is further parsed by the template, because we don’t have access
        # to the URL replacer here.  (Issue #1473)
        return image_path

    def source_ext(self, prefix=False):
        """Return the source file extension.

        If `prefix` is True, a `.src.` prefix will be added to the resulting extension
        if it's equal to the destination extension.
        """
        ext = os.path.splitext(self.source_path)[1]
        # do not publish PHP sources
        if prefix and ext == '.html':
            # ext starts with a dot
            return '.src' + ext
        else:
            return ext

# Code that fetches metadata from different places


def re_meta(line, match=None):
    """Find metadata using regular expressions."""
    if match:
        reStr = re.compile('^\.\. {0}: (.*)'.format(re.escape(match)))
    else:
        reStr = re.compile('^\.\. (.*?): (.*)')
    result = reStr.findall(line.strip())
    if match and result:
        return (match, result[0])
    elif not match and result:
        return (result[0][0], result[0][1].strip())
    else:
        return (None,)


def _get_metadata_from_filename_by_regex(filename, metadata_regexp, unslugify_titles, lang):
    """Try to reed the metadata from the filename based on the given re.

    This requires to use symbolic group names in the pattern.
    The part to read the metadata from the filename based on a regular
    expression is taken from Pelican - pelican/readers.py
    """
    match = re.match(metadata_regexp, filename)
    meta = {}

    if match:
        # .items() for py3k compat.
        for key, value in match.groupdict().items():
            k = key.lower().strip()  # metadata must be lowercase
            if k == 'title' and unslugify_titles:
                meta[k] = unslugify(value, lang, discard_numbers=False)
            else:
                meta[k] = value

    return meta


def get_metadata_from_file(source_path, config=None, lang=None):
    """Extract metadata from the file itself, by parsing contents."""
    try:
        if lang and config:
            source_path = get_translation_candidate(config, source_path, lang)
        elif lang:
            source_path += '.' + lang
        with io.open(source_path, "r", encoding="utf-8-sig") as meta_file:
            meta_data = [x.strip() for x in meta_file.readlines()]
        return _get_metadata_from_file(meta_data)
    except (UnicodeDecodeError, UnicodeEncodeError):
        raise ValueError('Error reading {0}: Nikola only supports UTF-8 files'.format(source_path))
    except Exception:  # The file may not exist, for multilingual sites
        return {}


re_md_title = re.compile(r'^{0}([^{0}].*)'.format(re.escape('#')))
# Assuming rst titles are going to be at least 4 chars long
# otherwise this detects things like ''' wich breaks other markups.
re_rst_title = re.compile(r'^([{0}]{{4,}})'.format(re.escape(
    string.punctuation)))


def _get_title_from_contents(meta_data):
    """Extract title from file contents, LAST RESOURCE."""
    piece = meta_data[:]
    title = None
    for i, line in enumerate(piece):
        if re_rst_title.findall(line) and i > 0:
            title = meta_data[i - 1].strip()
            break
        if (re_rst_title.findall(line) and i >= 0 and
                re_rst_title.findall(meta_data[i + 2])):
            title = meta_data[i + 1].strip()
            break
        if re_md_title.findall(line):
            title = re_md_title.findall(line)[0]
            break
    return title


def _get_metadata_from_file(meta_data):
    """Extract metadata from a post's source file."""
    meta = {}
    if not meta_data:
        return meta

    # Skip up to one empty line at the beginning (for txt2tags)
    if not meta_data[0]:
        meta_data = meta_data[1:]

    # First, get metadata from the beginning of the file,
    # up to first empty line

    for i, line in enumerate(meta_data):
        if not line:
            break
        match = re_meta(line)
        if match[0]:
            meta[match[0]] = match[1]

    # If we have no title, try to get it from document
    if 'title' not in meta:
        t = _get_title_from_contents(meta_data)
        if t is not None:
            meta['title'] = t

    return meta


def get_metadata_from_meta_file(path, config=None, lang=None):
    """Take a post path, and gets data from a matching .meta file."""
    global _UPGRADE_METADATA_ADVERTISED
    meta_path = os.path.splitext(path)[0] + '.meta'
    if lang and config:
        meta_path = get_translation_candidate(config, meta_path, lang)
    elif lang:
        meta_path += '.' + lang
    if os.path.isfile(meta_path):
        with io.open(meta_path, "r", encoding="utf8") as meta_file:
            meta_data = meta_file.readlines()

        # Detect new-style metadata.
        newstyleregexp = re.compile(r'\.\. .*?: .*')
        newstylemeta = False
        for l in meta_data:
            if l.strip():
                if re.match(newstyleregexp, l):
                    newstylemeta = True

        if newstylemeta:
            # New-style metadata is basically the same as reading metadata from
            # a 1-file post.
            return get_metadata_from_file(path, config, lang), newstylemeta
        else:
            if not _UPGRADE_METADATA_ADVERTISED:
                LOGGER.warn("Some posts on your site have old-style metadata. You should upgrade them to the new format, with support for extra fields.")
                LOGGER.warn("Install the 'upgrade_metadata' plugin (with 'nikola plugin -i upgrade_metadata') and run 'nikola upgrade_metadata'.")
                _UPGRADE_METADATA_ADVERTISED = True
            while len(meta_data) < 7:
                meta_data.append("")
            (title, slug, date, tags, link, description, _type) = [
                x.strip() for x in meta_data][:7]

            meta = {}

            if title:
                meta['title'] = title
            if slug:
                meta['slug'] = slug
            if date:
                meta['date'] = date
            if tags:
                meta['tags'] = tags
            if link:
                meta['link'] = link
            if description:
                meta['description'] = description
            if _type:
                meta['type'] = _type

            return meta, newstylemeta

    elif lang:
        # Metadata file doesn't exist, but not default language,
        # So, if default language metadata exists, return that.
        # This makes the 2-file format detection more reliable (Issue #525)
        return get_metadata_from_meta_file(path, config, lang=None)
    else:
        return {}, True


def get_meta(post, file_metadata_regexp=None, unslugify_titles=False, lang=None):
    """Get post's meta from source.

    If ``file_metadata_regexp`` is given it will be tried to read
    metadata from the filename.
    If ``unslugify_titles`` is True, the extracted title (if any) will be unslugified, as is done in galleries.
    If any metadata is then found inside the file the metadata from the
    file will override previous findings.
    """
    meta = defaultdict(lambda: '')

    try:
        config = post.config
    except AttributeError:
        config = None

    _, newstylemeta = get_metadata_from_meta_file(post.metadata_path, config, lang)
    meta.update(_)

    if not meta:
        post.is_two_file = False

    if file_metadata_regexp is not None:
        meta.update(_get_metadata_from_filename_by_regex(post.source_path,
                                                         file_metadata_regexp,
                                                         unslugify_titles,
                                                         post.default_lang))

    compiler_meta = {}

    if getattr(post, 'compiler', None):
        compiler_meta = post.compiler.read_metadata(post, file_metadata_regexp, unslugify_titles, lang)
        meta.update(compiler_meta)

    if not post.is_two_file and not compiler_meta:
        # Meta file has precedence over file, which can contain garbage.
        # Moreover, we should not to talk to the file if we have compiler meta.
        meta.update(get_metadata_from_file(post.source_path, config, lang))

    if lang is None:
        # Only perform these checks for the default language

        if 'slug' not in meta:
            # If no slug is found in the metadata use the filename
            meta['slug'] = slugify(unicode_str(os.path.splitext(
                os.path.basename(post.source_path))[0]), post.default_lang)

        if 'title' not in meta:
            # If no title is found, use the filename without extension
            meta['title'] = os.path.splitext(
                os.path.basename(post.source_path))[0]

    return meta, newstylemeta


def hyphenate(dom, _lang):
    """Hyphenate a post."""
    # circular import prevention
    from .nikola import LEGAL_VALUES
    lang = None
    if pyphen is not None:
        lang = LEGAL_VALUES['PYPHEN_LOCALES'].get(_lang, pyphen.language_fallback(_lang))
    else:
        utils.req_missing(['pyphen'], 'hyphenate texts', optional=True)
    hyphenator = None
    if pyphen is not None and lang is not None:
        # If pyphen does exist, we tell the user when configuring the site.
        # If it does not support a language, we ignore it quietly.
        try:
            hyphenator = pyphen.Pyphen(lang=lang)
        except KeyError:
            LOGGER.error("Cannot find hyphenation dictoniaries for {0} (from {1}).".format(lang, _lang))
            LOGGER.error("Pyphen cannot be installed to ~/.local (pip install --user).")
    if hyphenator is not None:
        for tag in ('p', 'li', 'span'):
            for node in dom.xpath("//%s[not(parent::pre)]" % tag):
                skip_node = False
                skippable_nodes = ['kbd', 'code', 'samp', 'mark', 'math', 'data', 'ruby', 'svg']
                if node.getchildren():
                    for child in node.getchildren():
                        if child.tag in skippable_nodes or (child.tag == 'span' and 'math' in child.get('class', [])):
                            skip_node = True
                elif 'math' in node.get('class', []):
                    skip_node = True
                if not skip_node:
                    insert_hyphens(node, hyphenator)
    return dom


def insert_hyphens(node, hyphenator):
    """Insert hyphens into a node."""
    textattrs = ('text', 'tail')
    if isinstance(node, lxml.etree._Entity):
        # HTML entities have no .text
        textattrs = ('tail',)
    for attr in textattrs:
        text = getattr(node, attr)
        if not text:
            continue
        new_data = ' '.join([hyphenator.inserted(w, hyphen='\u00AD')
                             for w in text.split(' ')])
        # Spaces are trimmed, we have to add them manually back
        if text[0].isspace():
            new_data = ' ' + new_data
        if text[-1].isspace():
            new_data += ' '
        setattr(node, attr, new_data)

    for child in node.iterchildren():
        insert_hyphens(child, hyphenator)


CRYPT = string.Template("""\
<script>
function rc4(key, str) {
    var s = [], j = 0, x, res = '';
    for (var i = 0; i < 256; i++) {
        s[i] = i;
    }
    for (i = 0; i < 256; i++) {
        j = (j + s[i] + key.charCodeAt(i % key.length)) % 256;
        x = s[i];
        s[i] = s[j];
        s[j] = x;
    }
    i = 0;
    j = 0;
    for (var y = 0; y < str.length; y++) {
        i = (i + 1) % 256;
        j = (j + s[i]) % 256;
        x = s[i];
        s[i] = s[j];
        s[j] = x;
        res += String.fromCharCode(str.charCodeAt(y) ^ s[(s[i] + s[j]) % 256]);
    }
    return res;
}
function decrypt() {
    key = $$("#key").val();
    crypt_div = $$("#encr")
    crypted = crypt_div.html();
    decrypted = rc4(key, window.atob(crypted));
    if (decrypted.substr(decrypted.length - 11) == "<!--tail-->"){
        crypt_div.html(decrypted);
        $$("#pwform").hide();
        crypt_div.show();
    } else { alert("Wrong password"); };
}
</script>

<div id="encr" style="display: none;">${data}</div>
<div id="pwform">
<form onsubmit="javascript:decrypt(); return false;" class="form-inline">
<fieldset>
<legend>This post is password-protected.</legend>
<input type="password" id="key" placeholder="Type password here">
<button type="submit" class="btn">Show Content</button>
</fieldset>
</form>
</div>""")
