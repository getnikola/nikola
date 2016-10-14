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

"""The main Nikola site object."""

from __future__ import print_function, unicode_literals
import io
from collections import defaultdict
from copy import copy
from pkg_resources import resource_filename
import datetime
import locale
import os
import json
import sys
import natsort
import mimetypes
try:
    from urlparse import urlparse, urlsplit, urlunsplit, urljoin, unquote
except ImportError:
    from urllib.parse import urlparse, urlsplit, urlunsplit, urljoin, unquote  # NOQA

try:
    import pyphen
except ImportError:
    pyphen = None

import dateutil.tz
import logging
import PyRSS2Gen as rss
import lxml.etree
import lxml.html
from yapsy.PluginManager import PluginManager
from blinker import signal

from .post import Post  # NOQA
from .state import Persistor
from . import DEBUG, utils, shortcodes
from .plugin_categories import (
    Command,
    LateTask,
    PageCompiler,
    CompilerExtension,
    MarkdownExtension,
    RestExtension,
    ShortcodePlugin,
    Task,
    TaskMultiplier,
    TemplateSystem,
    SignalHandler,
    ConfigPlugin,
    PostScanner,
)

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

# Default "Read more..." link
DEFAULT_INDEX_READ_MORE_LINK = '<p class="more"><a href="{link}">{read_more}…</a></p>'
DEFAULT_FEED_READ_MORE_LINK = '<p><a href="{link}">{read_more}…</a> ({min_remaining_read})</p>'

# Default pattern for translation files' names
DEFAULT_TRANSLATIONS_PATTERN = '{path}.{lang}.{ext}'


config_changed = utils.config_changed

__all__ = ('Nikola',)

# We store legal values for some setting here.  For internal use.
LEGAL_VALUES = {
    'COMMENT_SYSTEM': [
        'disqus',
        'facebook',
        'googleplus',
        'intensedebate',
        'isso',
        'livefyre',
        'muut',
    ],
    'TRANSLATIONS': {
        'ar': 'Arabic',
        'az': 'Azerbaijani',
        'bg': 'Bulgarian',
        'bs': 'Bosnian',
        'ca': 'Catalan',
        ('cs', 'cz'): 'Czech',
        'da': 'Danish',
        'de': 'German',
        ('el', '!gr'): 'Greek',
        'en': 'English',
        'eo': 'Esperanto',
        'es': 'Spanish',
        'et': 'Estonian',
        'eu': 'Basque',
        'fa': 'Persian',
        'fi': 'Finnish',
        'fr': 'French',
        'gl': 'Galician',
        'he': 'Hebrew',
        'hi': 'Hindi',
        'hr': 'Croatian',
        'hu': 'Hungarian',
        'id': 'Indonesian',
        'it': 'Italian',
        ('ja', '!jp'): 'Japanese',
        'ko': 'Korean',
        'lt': 'Lithuanian',
        'nb': 'Norwegian (Bokmål)',
        'nl': 'Dutch',
        'pa': 'Punjabi',
        'pl': 'Polish',
        'pt': 'Portuguese',
        'pt_br': 'Portuguese (Brazil)',
        'ru': 'Russian',
        'sk': 'Slovak',
        'sl': 'Slovene',
        'sq': 'Albanian',
        'sr': 'Serbian (Cyrillic)',
        'sr_latin': 'Serbian (Latin)',
        'sv': 'Swedish',
        'te': 'Telugu',
        ('tr', '!tr_TR'): 'Turkish',
        'ur': 'Urdu',
        'uk': 'Ukrainian',
        'zh_cn': 'Chinese (Simplified)',
        'zh_tw': 'Chinese (Traditional)'
    },
    '_WINDOWS_LOCALE_GUESSES': {
        # TODO incomplete
        # some languages may need that the appropriate Microsoft Language Pack be installed.
        "ar": "Arabic",
        "az": "Azeri (Latin)",
        "bg": "Bulgarian",
        "bs": "Bosnian",
        "ca": "Catalan",
        "cs": "Czech",
        "da": "Danish",
        "de": "German",
        "el": "Greek",
        "en": "English",
        # "eo": "Esperanto", # Not available
        "es": "Spanish",
        "et": "Estonian",
        "eu": "Basque",
        "fa": "Persian",  # Persian
        "fi": "Finnish",
        "fr": "French",
        "gl": "Galician",
        "he": "Hebrew",
        "hi": "Hindi",
        "hr": "Croatian",
        "hu": "Hungarian",
        "id": "Indonesian",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "nb": "Norwegian",  # Not Bokmål, as Windows doesn't find it for unknown reasons.
        "nl": "Dutch",
        "pa": "Punjabi",
        "pl": "Polish",
        "pt": "Portuguese_Portugal",
        "pt_br": "Portuguese_Brazil",
        "ru": "Russian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "sq": "Albanian",
        "sr": "Serbian",
        "sr_latin": "Serbian (Latin)",
        "sv": "Swedish",
        "te": "Telugu",
        "tr": "Turkish",
        "uk": "Ukrainian",
        "ur": "Urdu",
        "zh_cn": "Chinese_China",  # Chinese (Simplified)
        "zh_tw": "Chinese_Taiwan",  # Chinese (Traditional)
    },
    '_TRANSLATIONS_WITH_COUNTRY_SPECIFIERS': {
        # This dict is used in `init` in case of locales that exist with a
        # country specifier.  If there is no other locale that has the same
        # language with a different country, ``nikola init`` (but nobody else!)
        # will accept it, warning the user about it.

        # This dict is currently empty.
    },
    'RTL_LANGUAGES': ('ar', 'fa', 'he', 'ur'),
    'COLORBOX_LOCALES': defaultdict(
        str,
        ar='ar',
        bg='bg',
        ca='ca',
        cs='cs',
        cz='cs',
        da='da',
        de='de',
        en='',
        es='es',
        et='et',
        fa='fa',
        fi='fi',
        fr='fr',
        he='he',
        hr='hr',
        hu='hu',
        id='id',
        it='it',
        ja='ja',
        ko='kr',  # kr is South Korea, ko is the Korean language
        lt='lt',
        nb='no',
        nl='nl',
        pl='pl',
        pt='pt-BR',  # hope nobody will mind
        pt_br='pt-BR',
        ru='ru',
        sk='sk',
        sl='si',  # country code is si, language code is sl, colorbox is wrong
        sr='sr',  # warning: this is serbian in Latin alphabet
        sr_latin='sr',
        sv='sv',
        tr='tr',
        uk='uk',
        zh_cn='zh-CN',
        zh_tw='zh-TW'
    ),
    'MOMENTJS_LOCALES': defaultdict(
        str,
        ar='ar',
        az='az',
        bg='bg',
        bn='bn',
        bs='bs',
        ca='ca',
        cs='cs',
        cz='cs',
        da='da',
        de='de',
        el='el',
        en='en',
        eo='eo',
        es='es',
        et='et',
        eu='eu',
        fa='fa',
        fi='fi',
        fr='fr',
        gl='gl',
        hi='hi',
        he='he',
        hr='hr',
        hu='hu',
        id='id',
        it='it',
        ja='ja',
        ko='ko',
        lt='lt',
        nb='nb',
        nl='nl',
        pl='pl',
        pt='pt',
        pt_br='pt-br',
        ru='ru',
        sk='sk',
        sl='sl',
        sq='sq',
        sr='sr-cyrl',
        sr_latin='sr',
        sv='sv',
        tr='tr',
        uk='uk',
        zh_cn='zh-cn',
        zh_tw='zh-tw'
    ),
    'PYPHEN_LOCALES': {
        'bg': 'bg',
        'ca': 'ca',
        'cs': 'cs',
        'cz': 'cs',
        'da': 'da',
        'de': 'de',
        'el': 'el',
        'en': 'en_US',
        'es': 'es',
        'et': 'et',
        'fr': 'fr',
        'hr': 'hr',
        'hu': 'hu',
        'it': 'it',
        'lt': 'lt',
        'nb': 'nb',
        'nl': 'nl',
        'pl': 'pl',
        'pt': 'pt',
        'pt_br': 'pt_BR',
        'ru': 'ru',
        'sk': 'sk',
        'sl': 'sl',
        'sr': 'sr',
        'sv': 'sv',
        'te': 'te',
        'uk': 'uk',
    },
    'DOCUTILS_LOCALES': {
        'ca': 'ca',
        'da': 'da',
        'de': 'de',
        'en': 'en',
        'eo': 'eo',
        'es': 'es',
        'fi': 'fi',
        'fr': 'fr',
        'gl': 'gl',
        'he': 'he',
        'it': 'it',
        'ja': 'ja',
        'lt': 'lt',
        'pl': 'pl',
        'pt': 'pt_br',  # hope nobody will mind
        'pt_br': 'pt_br',
        'ru': 'ru',
        'sk': 'sk',
        'sv': 'sv',
        'zh_cn': 'zh_cn',
        'zh_tw': 'zh_tw'
    }
}


def _enclosure(post, lang):
    """Add an enclosure to RSS."""
    enclosure = post.meta('enclosure', lang)
    if enclosure:
        try:
            length = int(post.meta('enclosure_length', lang) or 0)
        except KeyError:
            length = 0
        except ValueError:
            utils.LOGGER.warn("Invalid enclosure length for post {0}".format(post.source_path))
            length = 0
        url = enclosure
        mime = mimetypes.guess_type(url)[0]
        return url, length, mime


class Nikola(object):
    """Class that handles site generation.

    Takes a site config as argument on creation.
    """

    def __init__(self, **config):
        """Setup proper environment for running tasks."""
        # Register our own path handlers
        self.path_handlers = {
            'slug': self.slug_path,
            'post_path': self.post_path,
            'root': self.root_path,
            'filename': self.filename_path,
        }

        self.strict = False
        self.posts = []
        self.all_posts = []
        self.posts_per_year = defaultdict(list)
        self.posts_per_month = defaultdict(list)
        self.posts_per_tag = defaultdict(list)
        self.posts_per_category = defaultdict(list)
        self.tags_per_language = defaultdict(list)
        self.post_per_file = {}
        self.timeline = []
        self.pages = []
        self._scanned = False
        self._template_system = None
        self._THEMES = None
        self._MESSAGES = None
        self.debug = DEBUG
        self.loghandlers = utils.STDERR_HANDLER  # TODO remove on v8
        self.colorful = config.pop('__colorful__', False)
        self.invariant = config.pop('__invariant__', False)
        self.quiet = config.pop('__quiet__', False)
        self._doit_config = config.pop('DOIT_CONFIG', {})
        self.original_cwd = config.pop('__cwd__', False)
        self.configuration_filename = config.pop('__configuration_filename__', False)
        self.configured = bool(config)
        self.injected_deps = defaultdict(list)
        self.shortcode_registry = {}

        self.rst_transforms = []
        self.template_hooks = {
            'extra_head': utils.TemplateHookRegistry('extra_head', self),
            'body_end': utils.TemplateHookRegistry('body_end', self),
            'page_header': utils.TemplateHookRegistry('page_header', self),
            'menu': utils.TemplateHookRegistry('menu', self),
            'menu_alt': utils.TemplateHookRegistry('menu_alt', self),
            'page_footer': utils.TemplateHookRegistry('page_footer', self),
        }

        # Maintain API
        utils.generic_rss_renderer = self.generic_rss_renderer

        # This is the default config
        self.config = {
            'ANNOTATIONS': False,
            'ARCHIVE_PATH': "",
            'ARCHIVE_FILENAME': "archive.html",
            'ARCHIVES_ARE_INDEXES': False,
            'AUTHOR_PATH': 'authors',
            'AUTHOR_PAGES_ARE_INDEXES': False,
            'AUTHOR_PAGES_DESCRIPTIONS': {},
            'AUTHORLIST_MINIMUM_POSTS': 1,
            'BLOG_AUTHOR': 'Default Author',
            'BLOG_TITLE': 'Default Title',
            'BLOG_DESCRIPTION': 'Default Description',
            'BODY_END': "",
            'CACHE_FOLDER': 'cache',
            'CATEGORY_PATH': None,  # None means: same as TAG_PATH
            'CATEGORY_PAGES_ARE_INDEXES': None,  # None means: same as TAG_PAGES_ARE_INDEXES
            'CATEGORY_PAGES_DESCRIPTIONS': {},
            'CATEGORY_PAGES_TITLES': {},
            'CATEGORY_PREFIX': 'cat_',
            'CATEGORY_ALLOW_HIERARCHIES': False,
            'CATEGORY_OUTPUT_FLAT_HIERARCHY': False,
            'CODE_COLOR_SCHEME': 'default',
            'COMMENT_SYSTEM': 'disqus',
            'COMMENTS_IN_GALLERIES': False,
            'COMMENTS_IN_PAGES': False,
            'COMPILERS': {
                "rest": ('.txt', '.rst'),
                "markdown": ('.md', '.mdown', '.markdown'),
                "textile": ('.textile',),
                "txt2tags": ('.t2t',),
                "bbcode": ('.bb',),
                "wiki": ('.wiki',),
                "ipynb": ('.ipynb',),
                "html": ('.html', '.htm')
            },
            'CONTENT_FOOTER': '',
            'CONTENT_FOOTER_FORMATS': {},
            'COPY_SOURCES': True,
            'CREATE_MONTHLY_ARCHIVE': False,
            'CREATE_SINGLE_ARCHIVE': False,
            'CREATE_FULL_ARCHIVES': False,
            'CREATE_DAILY_ARCHIVE': False,
            'DATE_FORMAT': '%Y-%m-%d %H:%M',
            'JS_DATE_FORMAT': 'YYYY-MM-DD HH:mm',
            'DATE_FANCINESS': 0,
            'DEFAULT_LANG': "en",
            'DEPLOY_COMMANDS': {'default': []},
            'DISABLED_PLUGINS': [],
            'EXTRA_PLUGINS_DIRS': [],
            'EXTRA_THEMES_DIRS': [],
            'COMMENT_SYSTEM_ID': 'nikolademo',
            'ENABLE_AUTHOR_PAGES': True,
            'EXIF_WHITELIST': {},
            'EXTRA_HEAD_DATA': '',
            'FAVICONS': (),
            'FEED_LENGTH': 10,
            'FILE_METADATA_REGEXP': None,
            'ADDITIONAL_METADATA': {},
            'FILES_FOLDERS': {'files': ''},
            'FILTERS': {},
            'FORCE_ISO8601': False,
            'FRONT_INDEX_HEADER': '',
            'GALLERY_FOLDERS': {'galleries': 'galleries'},
            'GALLERY_SORT_BY_DATE': True,
            'GLOBAL_CONTEXT_FILLER': [],
            'GZIP_COMMAND': None,
            'GZIP_FILES': False,
            'GZIP_EXTENSIONS': ('.txt', '.htm', '.html', '.css', '.js', '.json', '.xml'),
            'HIDDEN_AUTHORS': [],
            'HIDDEN_TAGS': [],
            'HIDDEN_CATEGORIES': [],
            'HYPHENATE': False,
            'IMAGE_FOLDERS': {'images': ''},
            'INDEX_DISPLAY_POST_COUNT': 10,
            'INDEX_FILE': 'index.html',
            'INDEX_TEASERS': False,
            'IMAGE_THUMBNAIL_SIZE': 400,
            'INDEXES_TITLE': "",
            'INDEXES_PAGES': "",
            'INDEXES_PAGES_MAIN': False,
            'INDEXES_PRETTY_PAGE_URL': False,
            'INDEXES_STATIC': True,
            'INDEX_PATH': '',
            'IPYNB_CONFIG': {},
            'KATEX_AUTO_RENDER': '',
            'LESS_COMPILER': 'lessc',
            'LESS_OPTIONS': [],
            'LICENSE': '',
            'LINK_CHECK_WHITELIST': [],
            'LISTINGS_FOLDERS': {'listings': 'listings'},
            'LOGO_URL': '',
            'NAVIGATION_LINKS': {},
            'MARKDOWN_EXTENSIONS': ['fenced_code', 'codehilite'],  # FIXME: Add 'extras' in v8
            'MAX_IMAGE_SIZE': 1280,
            'MATHJAX_CONFIG': '',
            'OLD_THEME_SUPPORT': True,
            'OUTPUT_FOLDER': 'output',
            'POSTS': (("posts/*.txt", "posts", "post.tmpl"),),
            'POSTS_SECTIONS': True,
            'POSTS_SECTION_COLORS': {},
            'POSTS_SECTION_ARE_INDEXES': True,
            'POSTS_SECTION_DESCRIPTIONS': "",
            'POSTS_SECTION_FROM_META': False,
            'POSTS_SECTION_NAME': "",
            'POSTS_SECTION_TITLE': "{name}",
            'PRESERVE_EXIF_DATA': False,
            # TODO: change in v8
            'PAGES': (("stories/*.txt", "stories", "story.tmpl"),),
            'PANDOC_OPTIONS': [],
            'PRETTY_URLS': False,
            'FUTURE_IS_NOW': False,
            'INDEX_READ_MORE_LINK': DEFAULT_INDEX_READ_MORE_LINK,
            'REDIRECTIONS': [],
            'ROBOTS_EXCLUSIONS': [],
            'GENERATE_ATOM': False,
            'FEED_TEASERS': True,
            'FEED_PLAIN': False,
            'FEED_PREVIEWIMAGE': True,
            'FEED_READ_MORE_LINK': DEFAULT_FEED_READ_MORE_LINK,
            'FEED_LINKS_APPEND_QUERY': False,
            'GENERATE_RSS': True,
            'RSS_LINK': None,
            'RSS_PATH': '',
            'SASS_COMPILER': 'sass',
            'SASS_OPTIONS': [],
            'SEARCH_FORM': '',
            'SHOW_BLOG_TITLE': True,
            'SHOW_SOURCELINK': True,
            'SHOW_UNTRANSLATED_POSTS': True,
            'SLUG_AUTHOR_PATH': True,
            'SLUG_TAG_PATH': True,
            'SOCIAL_BUTTONS_CODE': '',
            'SITE_URL': 'https://example.com/',
            'PAGE_INDEX': False,
            'STRIP_INDEXES': False,
            'SITEMAP_INCLUDE_FILELESS_DIRS': True,
            'TAG_PATH': 'categories',
            'TAG_PAGES_ARE_INDEXES': False,
            'TAG_PAGES_DESCRIPTIONS': {},
            'TAG_PAGES_TITLES': {},
            'TAGS_INDEX_PATH': '',
            'TAGLIST_MINIMUM_POSTS': 1,
            'TEMPLATE_FILTERS': {},
            'THEME': 'bootstrap3',
            'THEME_COLOR': '#5670d4',  # light "corporate blue"
            'THEME_REVEAL_CONFIG_SUBTHEME': 'sky',
            'THEME_REVEAL_CONFIG_TRANSITION': 'cube',
            'THUMBNAIL_SIZE': 180,
            'UNSLUGIFY_TITLES': False,  # WARNING: conf.py.in overrides this with True for backwards compatibility
            'URL_TYPE': 'rel_path',
            'USE_BASE_TAG': False,
            'USE_BUNDLES': True,
            'USE_CDN': False,
            'USE_CDN_WARNING': True,
            'USE_FILENAME_AS_TITLE': True,
            'USE_KATEX': False,
            'USE_OPEN_GRAPH': True,
            'USE_SLUGIFY': True,
            'TIMEZONE': 'UTC',
            'WRITE_TAG_CLOUD': True,
            'DEPLOY_DRAFTS': True,
            'DEPLOY_FUTURE': False,
            'SCHEDULE_ALL': False,
            'SCHEDULE_RULE': '',
            'LOGGING_HANDLERS': {'stderr': {'loglevel': 'WARNING', 'bubble': True}},
            'DEMOTE_HEADERS': 1,
            'GITHUB_SOURCE_BRANCH': 'master',
            'GITHUB_DEPLOY_BRANCH': 'gh-pages',
            'GITHUB_REMOTE_NAME': 'origin',
            'GITHUB_COMMIT_SOURCE': False,  # WARNING: conf.py.in overrides this with True for backwards compatibility
        }

        # set global_context for template rendering
        self._GLOBAL_CONTEXT = {}

        self.config.update(config)

        # __builtins__ contains useless cruft
        if '__builtins__' in self.config:
            try:
                del self.config['__builtins__']
            except KeyError:
                del self.config[b'__builtins__']

        self.config['__colorful__'] = self.colorful
        self.config['__invariant__'] = self.invariant
        self.config['__quiet__'] = self.quiet

        # Make sure we have sane NAVIGATION_LINKS.
        if not self.config['NAVIGATION_LINKS']:
            self.config['NAVIGATION_LINKS'] = {self.config['DEFAULT_LANG']: ()}

        # Translatability configuration.
        self.config['TRANSLATIONS'] = self.config.get('TRANSLATIONS',
                                                      {self.config['DEFAULT_LANG']: ''})
        utils.TranslatableSetting.default_lang = self.config['DEFAULT_LANG']

        self.TRANSLATABLE_SETTINGS = ('BLOG_AUTHOR',
                                      'BLOG_TITLE',
                                      'BLOG_DESCRIPTION',
                                      'LICENSE',
                                      'CONTENT_FOOTER',
                                      'SOCIAL_BUTTONS_CODE',
                                      'SEARCH_FORM',
                                      'BODY_END',
                                      'EXTRA_HEAD_DATA',
                                      'NAVIGATION_LINKS',
                                      'FRONT_INDEX_HEADER',
                                      'INDEX_READ_MORE_LINK',
                                      'FEED_READ_MORE_LINK',
                                      'INDEXES_TITLE',
                                      'POSTS_SECTION_COLORS',
                                      'POSTS_SECTION_DESCRIPTIONS',
                                      'POSTS_SECTION_NAME',
                                      'POSTS_SECTION_TITLE',
                                      'INDEXES_PAGES',
                                      'INDEXES_PRETTY_PAGE_URL',
                                      # PATH options (Issue #1914)
                                      'TAG_PATH',
                                      'TAGS_INDEX_PATH',
                                      'CATEGORY_PATH',
                                      'DATE_FORMAT',
                                      'JS_DATE_FORMAT',
                                      )

        self._GLOBAL_CONTEXT_TRANSLATABLE = ('blog_author',
                                             'blog_title',
                                             'blog_desc',  # TODO: remove in v8
                                             'blog_description',
                                             'license',
                                             'content_footer',
                                             'social_buttons_code',
                                             'search_form',
                                             'body_end',
                                             'extra_head_data',
                                             'date_format',
                                             'js_date_format',
                                             'posts_section_colors',
                                             'posts_section_descriptions',
                                             'posts_section_name',
                                             'posts_section_title',
                                             'front_index_header',
                                             )
        # WARNING: navigation_links SHOULD NOT be added to the list above.
        #          Themes ask for [lang] there and we should provide it.

        # We first have to massage JS_DATE_FORMAT, otherwise we run into trouble
        if 'JS_DATE_FORMAT' in self.config:
            if isinstance(self.config['JS_DATE_FORMAT'], dict):
                for k in self.config['JS_DATE_FORMAT']:
                    self.config['JS_DATE_FORMAT'][k] = json.dumps(self.config['JS_DATE_FORMAT'][k])
            else:
                self.config['JS_DATE_FORMAT'] = json.dumps(self.config['JS_DATE_FORMAT'])

        for i in self.TRANSLATABLE_SETTINGS:
            try:
                self.config[i] = utils.TranslatableSetting(i, self.config[i], self.config['TRANSLATIONS'])
            except KeyError:
                pass

        # A EXIF_WHITELIST implies you want to keep EXIF data
        if self.config['EXIF_WHITELIST'] and not self.config['PRESERVE_EXIF_DATA']:
            utils.LOGGER.warn('Setting EXIF_WHITELIST implies PRESERVE_EXIF_DATA is set to True')
            self.config['PRESERVE_EXIF_DATA'] = True

        # Setting PRESERVE_EXIF_DATA with an empty EXIF_WHITELIST implies 'keep everything'
        if self.config['PRESERVE_EXIF_DATA'] and not self.config['EXIF_WHITELIST']:
            utils.LOGGER.warn('You are setting PRESERVE_EXIF_DATA and not EXIF_WHITELIST so EXIF data is not really kept.')

        # Handle CONTENT_FOOTER properly.
        # We provide the arguments to format in CONTENT_FOOTER_FORMATS.
        self.config['CONTENT_FOOTER'].langformat(self.config['CONTENT_FOOTER_FORMATS'])

        # propagate USE_SLUGIFY
        utils.USE_SLUGIFY = self.config['USE_SLUGIFY']

        # Make sure we have pyphen installed if we are using it
        if self.config.get('HYPHENATE') and pyphen is None:
            utils.LOGGER.warn('To use the hyphenation, you have to install '
                              'the "pyphen" package.')
            utils.LOGGER.warn('Setting HYPHENATE to False.')
            self.config['HYPHENATE'] = False

        # FIXME: Internally, we still use post_pages because it's a pain to change it
        self.config['post_pages'] = []
        for i1, i2, i3 in self.config['POSTS']:
            self.config['post_pages'].append([i1, i2, i3, True])
        for i1, i2, i3 in self.config['PAGES']:
            self.config['post_pages'].append([i1, i2, i3, False])

        # RSS_TEASERS has been replaced with FEED_TEASERS
        # TODO: remove on v8
        if 'RSS_TEASERS' in config:
            utils.LOGGER.warn('The RSS_TEASERS option is deprecated, use FEED_TEASERS instead.')
            if 'FEED_TEASERS' in config:
                utils.LOGGER.warn('FEED_TEASERS conflicts with RSS_TEASERS, ignoring RSS_TEASERS.')
            self.config['FEED_TEASERS'] = config['RSS_TEASERS']

        # RSS_PLAIN has been replaced with FEED_PLAIN
        # TODO: remove on v8
        if 'RSS_PLAIN' in config:
            utils.LOGGER.warn('The RSS_PLAIN option is deprecated, use FEED_PLAIN instead.')
            if 'FEED_PLAIN' in config:
                utils.LOGGER.warn('FEED_PLIN conflicts with RSS_PLAIN, ignoring RSS_PLAIN.')
            self.config['FEED_PLAIN'] = config['RSS_PLAIN']

        # RSS_LINKS_APPEND_QUERY has been replaced with FEED_LINKS_APPEND_QUERY
        # TODO: remove on v8
        if 'RSS_LINKS_APPEND_QUERY' in config:
            utils.LOGGER.warn('The RSS_LINKS_APPEND_QUERY option is deprecated, use FEED_LINKS_APPEND_QUERY instead.')
            if 'FEED_LINKS_APPEND_QUERY' in config:
                utils.LOGGER.warn('FEED_LINKS_APPEND_QUERY conflicts with RSS_LINKS_APPEND_QUERY, ignoring RSS_LINKS_APPEND_QUERY.')
            self.config['FEED_LINKS_APPEND_QUERY'] = config['RSS_LINKS_APPEND_QUERY']

        # RSS_READ_MORE_LINK has been replaced with FEED_READ_MORE_LINK
        # TODO: remove on v8
        if 'RSS_READ_MORE_LINK' in config:
            utils.LOGGER.warn('The RSS_READ_MORE_LINK option is deprecated, use FEED_READ_MORE_LINK instead.')
            if 'FEED_READ_MORE_LINK' in config:
                utils.LOGGER.warn('FEED_READ_MORE_LINK conflicts with RSS_READ_MORE_LINK, ignoring RSS_READ_MORE_LINK')
            self.config['FEED_READ_MORE_LINK'] = utils.TranslatableSetting('FEED_READ_MORE_LINK', config['RSS_READ_MORE_LINK'], self.config['TRANSLATIONS'])

        # DEFAULT_TRANSLATIONS_PATTERN was changed from "p.e.l" to "p.l.e"
        # TODO: remove on v8
        if 'TRANSLATIONS_PATTERN' not in self.config:
            if len(self.config.get('TRANSLATIONS', {})) > 1:
                utils.LOGGER.warn('You do not have a TRANSLATIONS_PATTERN set in your config, yet you have multiple languages.')
                utils.LOGGER.warn('Setting TRANSLATIONS_PATTERN to the pre-v6 default ("{path}.{ext}.{lang}").')
                utils.LOGGER.warn('Please add the proper pattern to your conf.py.  (The new default in v7 is "{0}".)'.format(DEFAULT_TRANSLATIONS_PATTERN))
                self.config['TRANSLATIONS_PATTERN'] = "{path}.{ext}.{lang}"
            else:
                # use v7 default there
                self.config['TRANSLATIONS_PATTERN'] = DEFAULT_TRANSLATIONS_PATTERN

        # HIDE_SOURCELINK has been replaced with the inverted SHOW_SOURCELINK
        # TODO: remove on v8
        if 'HIDE_SOURCELINK' in config:
            utils.LOGGER.warn('The HIDE_SOURCELINK option is deprecated, use SHOW_SOURCELINK instead.')
            if 'SHOW_SOURCELINK' in config:
                utils.LOGGER.warn('HIDE_SOURCELINK conflicts with SHOW_SOURCELINK, ignoring HIDE_SOURCELINK.')
            self.config['SHOW_SOURCELINK'] = not config['HIDE_SOURCELINK']

        # HIDE_UNTRANSLATED_POSTS has been replaced with the inverted SHOW_UNTRANSLATED_POSTS
        # TODO: remove on v8
        if 'HIDE_UNTRANSLATED_POSTS' in config:
            utils.LOGGER.warn('The HIDE_UNTRANSLATED_POSTS option is deprecated, use SHOW_UNTRANSLATED_POSTS instead.')
            if 'SHOW_UNTRANSLATED_POSTS' in config:
                utils.LOGGER.warn('HIDE_UNTRANSLATED_POSTS conflicts with SHOW_UNTRANSLATED_POSTS, ignoring HIDE_UNTRANSLATED_POSTS.')
            self.config['SHOW_UNTRANSLATED_POSTS'] = not config['HIDE_UNTRANSLATED_POSTS']

        # READ_MORE_LINK has been split into INDEX_READ_MORE_LINK and RSS_READ_MORE_LINK
        # TODO: remove on v8
        if 'READ_MORE_LINK' in config:
            utils.LOGGER.warn('The READ_MORE_LINK option is deprecated, use INDEX_READ_MORE_LINK and RSS_READ_MORE_LINK instead.')
            if 'INDEX_READ_MORE_LINK' in config:
                utils.LOGGER.warn('READ_MORE_LINK conflicts with INDEX_READ_MORE_LINK, ignoring READ_MORE_LINK.')
            else:
                self.config['INDEX_READ_MORE_LINK'] = utils.TranslatableSetting('INDEX_READ_MORE_LINK', config['READ_MORE_LINK'], self.config['TRANSLATIONS'])

            if 'RSS_READ_MORE_LINK' in config:
                utils.LOGGER.warn('READ_MORE_LINK conflicts with RSS_READ_MORE_LINK, ignoring READ_MORE_LINK.')
            else:
                self.config['RSS_READ_MORE_LINK'] = utils.TranslatableSetting('RSS_READ_MORE_LINK', config['READ_MORE_LINK'], self.config['TRANSLATIONS'])

        # Moot.it renamed themselves to muut.io
        # TODO: remove on v8?
        if self.config.get('COMMENT_SYSTEM') == 'moot':
            utils.LOGGER.warn('The moot comment system has been renamed to muut by the upstream.  Setting COMMENT_SYSTEM to "muut".')
            self.config['COMMENT_SYSTEM'] = 'muut'

        # Disable RSS.  For a successful disable, we must have both the option
        # false and the plugin disabled through the official means.
        if 'generate_rss' in self.config['DISABLED_PLUGINS'] and self.config['GENERATE_RSS'] is True:
            self.config['GENERATE_RSS'] = False

        if not self.config['GENERATE_RSS'] and 'generate_rss' not in self.config['DISABLED_PLUGINS']:
            self.config['DISABLED_PLUGINS'].append('generate_rss')

        # PRETTY_URLS defaults to enabling STRIP_INDEXES unless explicitly disabled
        if self.config.get('PRETTY_URLS') and 'STRIP_INDEXES' not in config:
            self.config['STRIP_INDEXES'] = True

        if 'LISTINGS_FOLDER' in config:
            if 'LISTINGS_FOLDERS' not in config:
                utils.LOGGER.warn("The LISTINGS_FOLDER option is deprecated, use LISTINGS_FOLDERS instead.")
                self.config['LISTINGS_FOLDERS'] = {self.config['LISTINGS_FOLDER']: self.config['LISTINGS_FOLDER']}
                utils.LOGGER.warn("LISTINGS_FOLDERS = {0}".format(self.config['LISTINGS_FOLDERS']))
            else:
                utils.LOGGER.warn("Both LISTINGS_FOLDER and LISTINGS_FOLDERS are specified, ignoring LISTINGS_FOLDER.")

        if 'GALLERY_PATH' in config:
            if 'GALLERY_FOLDERS' not in config:
                utils.LOGGER.warn("The GALLERY_PATH option is deprecated, use GALLERY_FOLDERS instead.")
                self.config['GALLERY_FOLDERS'] = {self.config['GALLERY_PATH']: self.config['GALLERY_PATH']}
                utils.LOGGER.warn("GALLERY_FOLDERS = {0}".format(self.config['GALLERY_FOLDERS']))
            else:
                utils.LOGGER.warn("Both GALLERY_PATH and GALLERY_FOLDERS are specified, ignoring GALLERY_PATH.")

        if not self.config.get('COPY_SOURCES'):
            self.config['SHOW_SOURCELINK'] = False

        if self.config['CATEGORY_PATH']._inp is None:
            self.config['CATEGORY_PATH'] = self.config['TAG_PATH']
        if self.config['CATEGORY_PAGES_ARE_INDEXES'] is None:
            self.config['CATEGORY_PAGES_ARE_INDEXES'] = self.config['TAG_PAGES_ARE_INDEXES']

        self.default_lang = self.config['DEFAULT_LANG']
        self.translations = self.config['TRANSLATIONS']

        locale_fallback, locale_default, locales = sanitized_locales(
            self.config.get('LOCALE_FALLBACK', None),
            self.config.get('LOCALE_DEFAULT', None),
            self.config.get('LOCALES', {}), self.translations)
        utils.LocaleBorg.initialize(locales, self.default_lang)

        # BASE_URL defaults to SITE_URL
        if 'BASE_URL' not in self.config:
            self.config['BASE_URL'] = self.config.get('SITE_URL')
        # BASE_URL should *always* end in /
        if self.config['BASE_URL'] and self.config['BASE_URL'][-1] != '/':
            utils.LOGGER.warn("Your BASE_URL doesn't end in / -- adding it, but please fix it in your config file!")
            self.config['BASE_URL'] += '/'

        try:
            _bnl = urlsplit(self.config['BASE_URL']).netloc
            _bnl.encode('ascii')
            urlsplit(self.config['SITE_URL']).netloc.encode('ascii')
        except (UnicodeEncodeError, UnicodeDecodeError):
            utils.LOGGER.error("Your BASE_URL or SITE_URL contains an IDN expressed in Unicode.  Please convert it to Punycode.")
            utils.LOGGER.error("Punycode of {}: {}".format(_bnl, _bnl.encode('idna')))
            sys.exit(1)

        # TODO: remove in v8
        if not isinstance(self.config['DEPLOY_COMMANDS'], dict):
            utils.LOGGER.warn("A single list as DEPLOY_COMMANDS is deprecated.  DEPLOY_COMMANDS should be a dict, with deploy preset names as keys and lists of commands as values.")
            utils.LOGGER.warn("The key `default` is used by `nikola deploy`:")
            self.config['DEPLOY_COMMANDS'] = {'default': self.config['DEPLOY_COMMANDS']}
            utils.LOGGER.warn("DEPLOY_COMMANDS = {0}".format(self.config['DEPLOY_COMMANDS']))
            utils.LOGGER.info("(The above can be used with `nikola deploy` or `nikola deploy default`.  Multiple presets are accepted.)")

        # TODO: remove and change default in v8
        if 'BLOG_TITLE' in config and 'WRITE_TAG_CLOUD' not in config:
            # BLOG_TITLE is a hack, otherwise the warning would be displayed
            # when conf.py does not exist
            utils.LOGGER.warn("WRITE_TAG_CLOUD is not set in your config.  Defaulting to True (== writing tag_cloud_data.json).")
            utils.LOGGER.warn("Please explicitly add the setting to your conf.py with the desired value, as the setting will default to False in the future.")

        # Rename stories to pages (#1891, #2518)
        # TODO: remove in v8
        if 'COMMENTS_IN_STORIES' in config:
            utils.LOGGER.warn('The COMMENTS_IN_STORIES option is deprecated, use COMMENTS_IN_PAGES instead.')
            self.config['COMMENTS_IN_PAGES'] = config['COMMENTS_IN_STORIES']
        if 'STORY_INDEX' in config:
            utils.LOGGER.warn('The STORY_INDEX option is deprecated, use PAGE_INDEX instead.')
            self.config['PAGE_INDEX'] = config['STORY_INDEX']

        # We use one global tzinfo object all over Nikola.
        try:
            self.tzinfo = dateutil.tz.gettz(self.config['TIMEZONE'])
        except Exception as exc:
            utils.LOGGER.warn("Error getting TZ: {}", exc)
            self.tzinfo = dateutil.tz.gettz()
        self.config['__tzinfo__'] = self.tzinfo

        # Store raw compilers for internal use (need a copy for that)
        self.config['_COMPILERS_RAW'] = {}
        for k, v in self.config['COMPILERS'].items():
            self.config['_COMPILERS_RAW'][k] = list(v)

        compilers = defaultdict(set)
        # Also add aliases for combinations with TRANSLATIONS_PATTERN
        for compiler, exts in self.config['COMPILERS'].items():
            for ext in exts:
                compilers[compiler].add(ext)
                for lang in self.config['TRANSLATIONS'].keys():
                    candidate = utils.get_translation_candidate(self.config, "f" + ext, lang)
                    compilers[compiler].add(candidate)

        # Get search path for themes
        self.themes_dirs = ['themes'] + self.config['EXTRA_THEMES_DIRS']

        # Avoid redundant compilers
        # Remove compilers that match nothing in POSTS/PAGES
        # And put them in "bad compilers"
        pp_exts = set([os.path.splitext(x[0])[1] for x in self.config['post_pages']])
        self.config['COMPILERS'] = {}
        self.disabled_compilers = {}
        self.bad_compilers = set([])
        for k, v in compilers.items():
            if pp_exts.intersection(v):
                self.config['COMPILERS'][k] = sorted(list(v))
            else:
                self.bad_compilers.add(k)

        self._set_global_context_from_config()
        self._set_global_context_from_data()

        # Set persistent state facility
        self.state = Persistor('state_data.json')

        # Set cache facility
        self.cache = Persistor(os.path.join(self.config['CACHE_FOLDER'], 'cache_data.json'))

        # Create directories for persistors only if a site exists (Issue #2334)
        if self.configured:
            self.state._set_site(self)
            self.cache._set_site(self)

    def init_plugins(self, commands_only=False, load_all=False):
        """Load plugins as needed."""
        self.plugin_manager = PluginManager(categories_filter={
            "Command": Command,
            "Task": Task,
            "LateTask": LateTask,
            "TemplateSystem": TemplateSystem,
            "PageCompiler": PageCompiler,
            "TaskMultiplier": TaskMultiplier,
            "CompilerExtension": CompilerExtension,
            "MarkdownExtension": MarkdownExtension,
            "RestExtension": RestExtension,
            "ShortcodePlugin": ShortcodePlugin,
            "SignalHandler": SignalHandler,
            "ConfigPlugin": ConfigPlugin,
            "PostScanner": PostScanner,
        })
        self.plugin_manager.getPluginLocator().setPluginInfoExtension('plugin')
        extra_plugins_dirs = self.config['EXTRA_PLUGINS_DIRS']
        if sys.version_info[0] == 3:
            self._plugin_places = [
                resource_filename('nikola', 'plugins'),
                os.path.expanduser('~/.nikola/plugins'),
                os.path.join(os.getcwd(), 'plugins'),
            ] + [path for path in extra_plugins_dirs if path]
        else:
            self._plugin_places = [
                resource_filename('nikola', utils.sys_encode('plugins')),
                os.path.join(os.getcwd(), utils.sys_encode('plugins')),
                os.path.expanduser('~/.nikola/plugins'),
            ] + [utils.sys_encode(path) for path in extra_plugins_dirs if path]

        self.plugin_manager.getPluginLocator().setPluginPlaces(self._plugin_places)
        self.plugin_manager.locatePlugins()
        bad_candidates = set([])
        if not load_all:
            for p in self.plugin_manager._candidates:
                if commands_only:
                    if p[-1].details.has_option('Nikola', 'plugincategory'):
                        # FIXME TemplateSystem should not be needed
                        if p[-1].details.get('Nikola', 'PluginCategory') not in {'Command', 'Template'}:
                            bad_candidates.add(p)
                    else:
                        bad_candidates.add(p)
                elif self.configured:  # Not commands-only, and configured
                    # Remove compilers we don't use
                    if p[-1].name in self.bad_compilers:
                        bad_candidates.add(p)
                        self.disabled_compilers[p[-1].name] = p
                        utils.LOGGER.debug('Not loading unneeded compiler {}', p[-1].name)
                    if p[-1].name not in self.config['COMPILERS'] and \
                            p[-1].details.has_option('Nikola', 'plugincategory') and p[-1].details.get('Nikola', 'PluginCategory') == 'Compiler':
                        bad_candidates.add(p)
                        self.disabled_compilers[p[-1].name] = p
                        utils.LOGGER.debug('Not loading unneeded compiler {}', p[-1].name)
                    # Remove blacklisted plugins
                    if p[-1].name in self.config['DISABLED_PLUGINS']:
                        bad_candidates.add(p)
                        utils.LOGGER.debug('Not loading disabled plugin {}', p[-1].name)
                    # Remove compiler extensions we don't need
                    if p[-1].details.has_option('Nikola', 'compiler') and p[-1].details.get('Nikola', 'compiler') in self.disabled_compilers:
                        bad_candidates.add(p)
                        utils.LOGGER.debug('Not loading compiler extension {}', p[-1].name)
            self.plugin_manager._candidates = list(set(self.plugin_manager._candidates) - bad_candidates)

        # Find repeated plugins and discard the less local copy
        def plugin_position_in_places(plugin):
            # plugin here is a tuple:
            # (path to the .plugin file, path to plugin module w/o .py, plugin metadata)
            for i, place in enumerate(self._plugin_places):
                if plugin[0].startswith(place):
                    return i

        plugin_dict = defaultdict(list)
        for data in self.plugin_manager._candidates:
            plugin_dict[data[2].name].append(data)
        self.plugin_manager._candidates = []
        for name, plugins in plugin_dict.items():
            if len(plugins) > 1:
                # Sort by locality
                plugins.sort(key=plugin_position_in_places)
                utils.LOGGER.debug("Plugin {} exists in multiple places, using {}".format(
                    plugins[-1][2].name, plugins[-1][0]))
            self.plugin_manager._candidates.append(plugins[-1])

        self.plugin_manager.loadPlugins()

        self._activate_plugins_of_category("SignalHandler")

        # Emit signal for SignalHandlers which need to start running immediately.
        signal('sighandlers_loaded').send(self)

        self._commands = {}

        command_plugins = self._activate_plugins_of_category("Command")
        for plugin_info in command_plugins:
            plugin_info.plugin_object.short_help = plugin_info.description
            self._commands[plugin_info.name] = plugin_info.plugin_object

        self._activate_plugins_of_category("PostScanner")
        self._activate_plugins_of_category("Task")
        self._activate_plugins_of_category("LateTask")
        self._activate_plugins_of_category("TaskMultiplier")

        # Activate all required compiler plugins
        self.compiler_extensions = self._activate_plugins_of_category("CompilerExtension")
        for plugin_info in self.plugin_manager.getPluginsOfCategory("PageCompiler"):
            if plugin_info.name in self.config["COMPILERS"].keys():
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)

        # Activate shortcode plugins
        self._activate_plugins_of_category("ShortcodePlugin")

        # Load compiler plugins
        self.compilers = {}
        self.inverse_compilers = {}

        for plugin_info in self.plugin_manager.getPluginsOfCategory(
                "PageCompiler"):
            self.compilers[plugin_info.name] = \
                plugin_info.plugin_object

        self._activate_plugins_of_category("ConfigPlugin")
        self._register_templated_shortcodes()
        signal('configured').send(self)

    def _set_global_context_from_config(self):
        """Create global context from configuration.

        These are options that are used by templates, so they always need to be
        available.
        """
        self._GLOBAL_CONTEXT['url_type'] = self.config['URL_TYPE']
        self._GLOBAL_CONTEXT['timezone'] = self.tzinfo
        self._GLOBAL_CONTEXT['_link'] = self.link
        try:
            self._GLOBAL_CONTEXT['set_locale'] = utils.LocaleBorg().set_locale
        except utils.LocaleBorgUninitializedException:
            self._GLOBAL_CONTEXT['set_locale'] = None
        self._GLOBAL_CONTEXT['rel_link'] = self.rel_link
        self._GLOBAL_CONTEXT['abs_link'] = self.abs_link
        self._GLOBAL_CONTEXT['exists'] = self.file_exists
        self._GLOBAL_CONTEXT['SLUG_AUTHOR_PATH'] = self.config['SLUG_AUTHOR_PATH']
        self._GLOBAL_CONTEXT['SLUG_TAG_PATH'] = self.config['SLUG_TAG_PATH']
        self._GLOBAL_CONTEXT['annotations'] = self.config['ANNOTATIONS']
        self._GLOBAL_CONTEXT['index_display_post_count'] = self.config[
            'INDEX_DISPLAY_POST_COUNT']
        self._GLOBAL_CONTEXT['index_file'] = self.config['INDEX_FILE']
        self._GLOBAL_CONTEXT['use_base_tag'] = self.config['USE_BASE_TAG']
        self._GLOBAL_CONTEXT['use_bundles'] = self.config['USE_BUNDLES']
        self._GLOBAL_CONTEXT['use_cdn'] = self.config.get("USE_CDN")
        self._GLOBAL_CONTEXT['theme_color'] = self.config.get("THEME_COLOR")
        self._GLOBAL_CONTEXT['favicons'] = self.config['FAVICONS']
        self._GLOBAL_CONTEXT['date_format'] = self.config.get('DATE_FORMAT')
        self._GLOBAL_CONTEXT['blog_author'] = self.config.get('BLOG_AUTHOR')
        self._GLOBAL_CONTEXT['blog_title'] = self.config.get('BLOG_TITLE')
        self._GLOBAL_CONTEXT['show_blog_title'] = self.config.get('SHOW_BLOG_TITLE')
        self._GLOBAL_CONTEXT['logo_url'] = self.config.get('LOGO_URL')
        self._GLOBAL_CONTEXT['blog_description'] = self.config.get('BLOG_DESCRIPTION')
        self._GLOBAL_CONTEXT['front_index_header'] = self.config.get('FRONT_INDEX_HEADER')
        self._GLOBAL_CONTEXT['color_hsl_adjust_hex'] = utils.color_hsl_adjust_hex
        self._GLOBAL_CONTEXT['colorize_str_from_base_color'] = utils.colorize_str_from_base_color

        # TODO: remove in v8
        self._GLOBAL_CONTEXT['blog_desc'] = self.config.get('BLOG_DESCRIPTION')

        self._GLOBAL_CONTEXT['blog_url'] = self.config.get('SITE_URL')
        self._GLOBAL_CONTEXT['template_hooks'] = self.template_hooks
        self._GLOBAL_CONTEXT['body_end'] = self.config.get('BODY_END')
        self._GLOBAL_CONTEXT['social_buttons_code'] = self.config.get('SOCIAL_BUTTONS_CODE')
        self._GLOBAL_CONTEXT['translations'] = self.config.get('TRANSLATIONS')
        self._GLOBAL_CONTEXT['license'] = self.config.get('LICENSE')
        self._GLOBAL_CONTEXT['search_form'] = self.config.get('SEARCH_FORM')
        self._GLOBAL_CONTEXT['comment_system'] = self.config.get('COMMENT_SYSTEM')
        self._GLOBAL_CONTEXT['comment_system_id'] = self.config.get('COMMENT_SYSTEM_ID')
        self._GLOBAL_CONTEXT['site_has_comments'] = bool(self.config.get('COMMENT_SYSTEM'))
        self._GLOBAL_CONTEXT['mathjax_config'] = self.config.get(
            'MATHJAX_CONFIG')
        self._GLOBAL_CONTEXT['use_katex'] = self.config.get('USE_KATEX')
        self._GLOBAL_CONTEXT['katex_auto_render'] = self.config.get('KATEX_AUTO_RENDER')
        self._GLOBAL_CONTEXT['subtheme'] = self.config.get('THEME_REVEAL_CONFIG_SUBTHEME')
        self._GLOBAL_CONTEXT['transition'] = self.config.get('THEME_REVEAL_CONFIG_TRANSITION')
        self._GLOBAL_CONTEXT['content_footer'] = self.config.get(
            'CONTENT_FOOTER')
        self._GLOBAL_CONTEXT['generate_atom'] = self.config.get('GENERATE_ATOM')
        self._GLOBAL_CONTEXT['generate_rss'] = self.config.get('GENERATE_RSS')
        self._GLOBAL_CONTEXT['rss_path'] = self.config.get('RSS_PATH')
        self._GLOBAL_CONTEXT['rss_link'] = self.config.get('RSS_LINK')

        self._GLOBAL_CONTEXT['navigation_links'] = self.config.get('NAVIGATION_LINKS')

        self._GLOBAL_CONTEXT['use_open_graph'] = self.config.get(
            'USE_OPEN_GRAPH', True)
        self._GLOBAL_CONTEXT['twitter_card'] = self.config.get(
            'TWITTER_CARD', {})
        self._GLOBAL_CONTEXT['hide_sourcelink'] = not self.config.get(
            'SHOW_SOURCELINK')
        self._GLOBAL_CONTEXT['show_sourcelink'] = self.config.get(
            'SHOW_SOURCELINK')
        self._GLOBAL_CONTEXT['extra_head_data'] = self.config.get('EXTRA_HEAD_DATA')
        self._GLOBAL_CONTEXT['date_fanciness'] = self.config.get('DATE_FANCINESS')
        self._GLOBAL_CONTEXT['js_date_format'] = self.config.get('JS_DATE_FORMAT')
        self._GLOBAL_CONTEXT['colorbox_locales'] = LEGAL_VALUES['COLORBOX_LOCALES']
        self._GLOBAL_CONTEXT['momentjs_locales'] = LEGAL_VALUES['MOMENTJS_LOCALES']
        self._GLOBAL_CONTEXT['hidden_tags'] = self.config.get('HIDDEN_TAGS')
        self._GLOBAL_CONTEXT['hidden_categories'] = self.config.get('HIDDEN_CATEGORIES')
        self._GLOBAL_CONTEXT['hidden_authors'] = self.config.get('HIDDEN_AUTHORS')
        self._GLOBAL_CONTEXT['url_replacer'] = self.url_replacer
        self._GLOBAL_CONTEXT['posts_sections'] = self.config.get('POSTS_SECTIONS')
        self._GLOBAL_CONTEXT['posts_section_are_indexes'] = self.config.get('POSTS_SECTION_ARE_INDEXES')
        self._GLOBAL_CONTEXT['posts_section_colors'] = self.config.get('POSTS_SECTION_COLORS')
        self._GLOBAL_CONTEXT['posts_section_descriptions'] = self.config.get('POSTS_SECTION_DESCRIPTIONS')
        self._GLOBAL_CONTEXT['posts_section_from_meta'] = self.config.get('POSTS_SECTION_FROM_META')
        self._GLOBAL_CONTEXT['posts_section_name'] = self.config.get('POSTS_SECTION_NAME')
        self._GLOBAL_CONTEXT['posts_section_title'] = self.config.get('POSTS_SECTION_TITLE')

        # IPython theme configuration.  If a website has ipynb enabled in post_pages
        # we should enable the IPython CSS (leaving that up to the theme itself).

        self._GLOBAL_CONTEXT['needs_ipython_css'] = 'ipynb' in self.config['COMPILERS']

        self._GLOBAL_CONTEXT.update(self.config.get('GLOBAL_CONTEXT', {}))

    def _set_global_context_from_data(self):
        """Load files from data/ and put them in the global context."""
        self._GLOBAL_CONTEXT['data'] = {}
        for root, dirs, files in os.walk('data', followlinks=True):
            for fname in files:
                fname = os.path.join(root, fname)
                data = utils.load_data(fname)
                key = os.path.splitext(fname.split(os.sep, 1)[1])[0]
                self._GLOBAL_CONTEXT['data'][key] = data

    def _activate_plugins_of_category(self, category):
        """Activate all the plugins of a given category and return them."""
        # this code duplicated in tests/base.py
        plugins = []
        for plugin_info in self.plugin_manager.getPluginsOfCategory(category):
            self.plugin_manager.activatePluginByName(plugin_info.name)
            plugin_info.plugin_object.set_site(self)
            plugins.append(plugin_info)
        return plugins

    def _get_themes(self):
        if self._THEMES is None:
            try:
                self._THEMES = utils.get_theme_chain(self.config['THEME'], self.themes_dirs)
            except Exception:
                if self.config['THEME'] != 'bootstrap3':
                    utils.LOGGER.warn('''Cannot load theme "{0}", using 'bootstrap3' instead.'''.format(self.config['THEME']))
                    self.config['THEME'] = 'bootstrap3'
                    return self._get_themes()
                raise
            # Check consistency of USE_CDN and the current THEME (Issue #386)
            if self.config['USE_CDN'] and self.config['USE_CDN_WARNING']:
                bootstrap_path = utils.get_asset_path(os.path.join(
                    'assets', 'css', 'bootstrap.min.css'), self._THEMES)
                if bootstrap_path and bootstrap_path.split(os.sep)[-4] not in ['bootstrap', 'bootstrap3']:
                    utils.LOGGER.warn('The USE_CDN option may be incompatible with your theme, because it uses a hosted version of bootstrap.')

        return self._THEMES

    THEMES = property(_get_themes)

    def _get_messages(self):
        try:
            if self._MESSAGES is None:
                self._MESSAGES = utils.load_messages(self.THEMES,
                                                     self.translations,
                                                     self.default_lang,
                                                     themes_dirs=self.themes_dirs)
            return self._MESSAGES
        except utils.LanguageNotFoundError as e:
            utils.LOGGER.error('''Cannot load language "{0}".  Please make sure it is supported by Nikola itself, or that you have the appropriate messages files in your themes.'''.format(e.lang))
            sys.exit(1)

    MESSAGES = property(_get_messages)

    def _get_global_context(self):
        """Initialize some parts of GLOBAL_CONTEXT only when it's queried."""
        if 'messages' not in self._GLOBAL_CONTEXT:
            self._GLOBAL_CONTEXT['messages'] = self.MESSAGES
        if 'has_custom_css' not in self._GLOBAL_CONTEXT:
            # check if custom css exist and is not empty
            custom_css_path = utils.get_asset_path(
                'assets/css/custom.css',
                self.THEMES,
                self.config['FILES_FOLDERS']
            )
            if custom_css_path and self.file_exists(custom_css_path, not_empty=True):
                self._GLOBAL_CONTEXT['has_custom_css'] = True
            else:
                self._GLOBAL_CONTEXT['has_custom_css'] = False

        return self._GLOBAL_CONTEXT

    GLOBAL_CONTEXT = property(_get_global_context)

    def _get_template_system(self):
        if self._template_system is None:
            # Load template plugin
            template_sys_name = utils.get_template_engine(self.THEMES)
            pi = self.plugin_manager.getPluginByName(
                template_sys_name, "TemplateSystem")
            if pi is None:
                sys.stderr.write("Error loading {0} template system "
                                 "plugin\n".format(template_sys_name))
                sys.exit(1)
            self._template_system = pi.plugin_object
            lookup_dirs = ['templates'] + [os.path.join(utils.get_theme_path(name), "templates")
                                           for name in self.THEMES]
            self._template_system.set_directories(lookup_dirs,
                                                  self.config['CACHE_FOLDER'])
            self._template_system.set_site(self)
        return self._template_system

    template_system = property(_get_template_system)

    def get_compiler(self, source_name):
        """Get the correct compiler for a post from `conf.COMPILERS`.

        To make things easier for users, the mapping in conf.py is
        compiler->[extensions], although this is less convenient for us.
        The majority of this function is reversing that dictionary and error checking.
        """
        ext = os.path.splitext(source_name)[1]
        try:
            compile_html = self.inverse_compilers[ext]
        except KeyError:
            # Find the correct compiler for this files extension
            lang_exts_tab = list(self.config['COMPILERS'].items())
            langs = [lang for lang, exts in lang_exts_tab if ext in exts or
                     len([ext_ for ext_ in exts if source_name.endswith(ext_)]) > 0]
            if len(langs) != 1:
                if len(set(langs)) > 1:
                    exit("Your file extension->compiler definition is "
                         "ambiguous.\nPlease remove one of the file extensions "
                         "from 'COMPILERS' in conf.py\n(The error is in "
                         "one of {0})".format(', '.join(langs)))
                elif len(langs) > 1:
                    langs = langs[:1]
                else:
                    exit("COMPILERS in conf.py does not tell me how to "
                         "handle '{0}' extensions.".format(ext))

            lang = langs[0]
            try:
                compile_html = self.compilers[lang]
            except KeyError:
                exit("Cannot find '{0}' compiler; it might require an extra plugin -- do you have it installed?".format(lang))
            self.inverse_compilers[ext] = compile_html

        return compile_html

    def render_template(self, template_name, output_name, context, url_type=None):
        """Render a template with the global context.

        If ``output_name`` is None, will return a string and all URL
        normalization will be ignored (including the link:// scheme).
        If ``output_name`` is a string, URLs will be normalized and
        the resultant HTML will be saved to the named file (path must
        start with OUTPUT_FOLDER).

        The argument ``url_type`` allows to override the ``URL_TYPE``
        configuration.
        """
        local_context = {}
        local_context["template_name"] = template_name
        local_context.update(self.GLOBAL_CONTEXT)
        local_context.update(context)
        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            local_context[k] = local_context[k](local_context['lang'])
        local_context['is_rtl'] = local_context['lang'] in LEGAL_VALUES['RTL_LANGUAGES']
        # string, arguments
        local_context["formatmsg"] = lambda s, *a: s % a
        for h in local_context['template_hooks'].values():
            h.context = context

        for func in self.config['GLOBAL_CONTEXT_FILLER']:
            func(local_context, template_name)

        data = self.template_system.render_template(
            template_name, None, local_context)

        if output_name is None:
            return data

        assert output_name.startswith(
            self.config["OUTPUT_FOLDER"])
        url_part = output_name[len(self.config["OUTPUT_FOLDER"]) + 1:]

        # Treat our site as if output/ is "/" and then make all URLs relative,
        # making the site "relocatable"
        src = os.sep + url_part
        src = os.path.normpath(src)
        # The os.sep is because normpath will change "/" to "\" on windows
        src = "/".join(src.split(os.sep))

        utils.makedirs(os.path.dirname(output_name))
        parser = lxml.html.HTMLParser(remove_blank_text=True)
        doc = lxml.html.document_fromstring(data, parser)
        self.rewrite_links(doc, src, context['lang'], url_type)
        data = b'<!DOCTYPE html>\n' + lxml.html.tostring(doc, encoding='utf8', method='html', pretty_print=True)
        with open(output_name, "wb+") as post_file:
            post_file.write(data)

    def rewrite_links(self, doc, src, lang, url_type=None):
        """Replace links in document to point to the right places."""
        # First let lxml replace most of them
        doc.rewrite_links(lambda dst: self.url_replacer(src, dst, lang, url_type), resolve_base_href=False)

        # lxml ignores srcset in img and source elements, so do that by hand
        objs = list(doc.xpath('(*//img|*//source)'))
        for obj in objs:
            if 'srcset' in obj.attrib:
                urls = [u.strip() for u in obj.attrib['srcset'].split(',')]
                urls = [self.url_replacer(src, dst, lang, url_type) for dst in urls]
                obj.set('srcset', ', '.join(urls))

    def url_replacer(self, src, dst, lang=None, url_type=None):
        """Mangle URLs.

        * Replaces link:// URLs with real links
        * Makes dst relative to src
        * Leaves fragments unchanged
        * Leaves full URLs unchanged
        * Avoids empty links

        src is the URL where this link is used
        dst is the link to be mangled
        lang is used for language-sensitive URLs in link://
        url_type is used to determine final link appearance, defaulting to URL_TYPE from config
        """
        parsed_src = urlsplit(src)
        src_elems = parsed_src.path.split('/')[1:]
        dst_url = urlparse(dst)
        if lang is None:
            lang = self.default_lang
        if url_type is None:
            url_type = self.config.get('URL_TYPE')

        if dst_url.scheme and dst_url.scheme not in ['http', 'https', 'link']:
            return dst

        # Refuse to replace links that are full URLs.
        if dst_url.netloc:
            if dst_url.scheme == 'link':  # Magic link
                dst = self.link(dst_url.netloc, dst_url.path.lstrip('/'), lang)
            # Assuming the site is served over one of these, and
            # since those are the only URLs we want to rewrite...
            else:
                if '%' in dst_url.netloc:
                    # convert lxml percent-encoded garbage to punycode
                    nl = unquote(dst_url.netloc)
                    try:
                        nl = nl.decode('utf-8')
                    except AttributeError:
                        # python 3: already unicode
                        pass
                    nl = nl.encode('idna')
                    if isinstance(nl, utils.bytes_str):
                        nl = nl.decode('latin-1')  # so idna stays unchanged
                    dst = urlunsplit((dst_url.scheme,
                                      nl,
                                      dst_url.path,
                                      dst_url.query,
                                      dst_url.fragment))
                return dst
        elif dst_url.scheme == 'link':  # Magic absolute path link:
            dst = dst_url.path
            return dst

        # Refuse to replace links that consist of a fragment only
        if ((not dst_url.scheme) and (not dst_url.netloc) and
                (not dst_url.path) and (not dst_url.params) and
                (not dst_url.query) and dst_url.fragment):
            return dst

        # Normalize
        dst = urljoin(src, dst)

        # Avoid empty links.
        if src == dst:
            if url_type == 'absolute':
                dst = urljoin(self.config['BASE_URL'], dst.lstrip('/'))
                return dst
            elif url_type == 'full_path':
                dst = urljoin(self.config['BASE_URL'], dst.lstrip('/'))
                return urlparse(dst).path
            else:
                return "#"

        # Check that link can be made relative, otherwise return dest
        parsed_dst = urlsplit(dst)
        if parsed_src[:2] != parsed_dst[:2]:
            if url_type == 'absolute':
                dst = urljoin(self.config['BASE_URL'], dst)
            return dst

        if url_type in ('full_path', 'absolute'):
            dst = urljoin(self.config['BASE_URL'], dst.lstrip('/'))
            if url_type == 'full_path':
                parsed = urlparse(urljoin(self.config['BASE_URL'], dst.lstrip('/')))
                if parsed.fragment:
                    dst = '{0}#{1}'.format(parsed.path, parsed.fragment)
                else:
                    dst = parsed.path
            return dst

        # Now both paths are on the same site and absolute
        dst_elems = parsed_dst.path.split('/')[1:]

        i = 0
        for (i, s), d in zip(enumerate(src_elems), dst_elems):
            if s != d:
                break
        # Now i is the longest common prefix
        result = '/'.join(['..'] * (len(src_elems) - i - 1) + dst_elems[i:])

        if not result and not parsed_dst.fragment:
            result = "."

        # Don't forget the query part of the link
        if parsed_dst.query:
            result += "?" + parsed_dst.query

        # Don't forget the fragment (anchor) part of the link
        if parsed_dst.fragment:
            result += "#" + parsed_dst.fragment

        assert result, (src, dst, i, src_elems, dst_elems)

        return result

    def _make_renderfunc(self, t_data, fname=None):
        """Return a function that can be registered as a template shortcode.

        The returned function has access to the passed template data and
        accepts any number of positional and keyword arguments. Positional
        arguments values are added as a tuple under the key ``_args`` to the
        keyword argument dict and then the latter provides the template
        context.

        """
        def render_shortcode(*args, **kw):
            context = self.GLOBAL_CONTEXT.copy()
            context.update(kw)
            context['_args'] = args
            context['lang'] = utils.LocaleBorg().current_lang
            for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
                context[k] = context[k](context['lang'])
            output = self.template_system.render_template_to_string(t_data, context)
            if fname is not None:
                dependencies = [fname] + self.template_system.get_deps(fname)
            else:
                dependencies = []
            return output, dependencies
        return render_shortcode

    def _register_templated_shortcodes(self):
        """Register shortcodes based on templates.

        This will register a shortcode for any template found in shortcodes/
        folders and a generic "template" shortcode which will consider the
        content in the shortcode as a template in itself.
        """
        self.register_shortcode('template', self._template_shortcode_handler)

        builtin_sc_dir = resource_filename(
            'nikola',
            os.path.join('data', 'shortcodes', utils.get_template_engine(self.THEMES)))

        for sc_dir in [builtin_sc_dir, 'shortcodes']:
            if not os.path.isdir(sc_dir):
                continue

            for fname in os.listdir(sc_dir):
                name, ext = os.path.splitext(fname)

                if ext != '.tmpl':
                    continue
                with open(os.path.join(sc_dir, fname)) as fd:
                    self.register_shortcode(name, self._make_renderfunc(
                        fd.read(), os.path.join(sc_dir, fname)))

    def _template_shortcode_handler(self, *args, **kw):
        t_data = kw.pop('data', '')
        context = self.GLOBAL_CONTEXT.copy()
        context.update(kw)
        context['_args'] = args
        context['lang'] = utils.LocaleBorg().current_lang
        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            context[k] = context[k](context['lang'])
        output = self.template_system.render_template_to_string(t_data, context)
        dependencies = self.template_system.get_string_deps(t_data)
        return output, dependencies

    def register_shortcode(self, name, f):
        """Register function f to handle shortcode "name"."""
        if name in self.shortcode_registry:
            utils.LOGGER.warn('Shortcode name conflict: {}', name)
            return
        self.shortcode_registry[name] = f

    # XXX in v8, get rid of with_dependencies
    def apply_shortcodes(self, data, filename=None, lang=None, with_dependencies=False, extra_context={}):
        """Apply shortcodes from the registry on data."""
        if lang is None:
            lang = utils.LocaleBorg().current_lang
        return shortcodes.apply_shortcodes(data, self.shortcode_registry, self, filename, lang=lang, with_dependencies=with_dependencies, extra_context=extra_context)

    def generic_rss_renderer(self, lang, title, link, description, timeline, output_path,
                             rss_teasers, rss_plain, feed_length=10, feed_url=None,
                             enclosure=_enclosure, rss_links_append_query=None):
        """Take all necessary data, and render a RSS feed in output_path."""
        rss_obj = utils.ExtendedRSS2(
            title=title,
            link=utils.encodelink(link),
            description=description,
            lastBuildDate=datetime.datetime.utcnow(),
            generator='https://getnikola.com/',
            language=lang
        )

        if feed_url:
            absurl = '/' + feed_url[len(self.config['BASE_URL']):]
            rss_obj.xsl_stylesheet_href = self.url_replacer(absurl, "/assets/xml/rss.xsl")

        items = []

        feed_append_query = None
        if rss_links_append_query:
            feed_append_query = rss_links_append_query.format(
                feedRelUri='/' + feed_url[len(self.config['BASE_URL']):],
                feedFormat="rss")

        for post in timeline[:feed_length]:
            data = post.text(lang, teaser_only=rss_teasers, strip_html=rss_plain,
                             feed_read_more_link=True, feed_links_append_query=feed_append_query)
            if feed_url is not None and data:
                # Massage the post's HTML (unless plain)
                if not rss_plain:
                    if self.config["FEED_PREVIEWIMAGE"] and 'previewimage' in post.meta[lang] and post.meta[lang]['previewimage'] not in data:
                        data = "<figure><img src=\"{}\"></figure> {}".format(post.meta[lang]['previewimage'], data)
                    # FIXME: this is duplicated with code in Post.text()
                    try:
                        doc = lxml.html.document_fromstring(data)
                        doc.rewrite_links(lambda dst: self.url_replacer(post.permalink(), dst, lang, 'absolute'))
                        try:
                            body = doc.body
                            data = (body.text or '') + ''.join(
                                [lxml.html.tostring(child, encoding='unicode')
                                    for child in body.iterchildren()])
                        except IndexError:  # No body there, it happens sometimes
                            data = ''
                    except lxml.etree.ParserError as e:
                        if str(e) == "Document is empty":
                            data = ""
                        else:  # let other errors raise
                            raise(e)
            args = {
                'title': post.title(lang),
                'link': post.permalink(lang, absolute=True, query=feed_append_query),
                'description': data,
                # PyRSS2Gen's pubDate is GMT time.
                'pubDate': (post.date if post.date.tzinfo is None else
                            post.date.astimezone(dateutil.tz.tzutc())),
                'categories': post._tags.get(lang, []),
                'creator': post.author(lang),
                'guid': post.permalink(lang, absolute=True),
            }

            if post.author(lang):
                rss_obj.rss_attrs["xmlns:dc"] = "http://purl.org/dc/elements/1.1/"

            if enclosure:
                # enclosure callback returns None if post has no enclosure, or a
                # 3-tuple of (url, length (0 is valid), mimetype)
                enclosure_details = enclosure(post=post, lang=lang)
                if enclosure_details is not None:
                    args['enclosure'] = rss.Enclosure(*enclosure_details)

            items.append(utils.ExtendedItem(**args))

        rss_obj.items = items
        rss_obj.self_url = feed_url
        rss_obj.rss_attrs["xmlns:atom"] = "http://www.w3.org/2005/Atom"

        dst_dir = os.path.dirname(output_path)
        utils.makedirs(dst_dir)
        with io.open(output_path, "w+", encoding="utf-8") as rss_file:
            data = rss_obj.to_xml(encoding='utf-8')
            if isinstance(data, utils.bytes_str):
                data = data.decode('utf-8')
            rss_file.write(data)

    def path(self, kind, name, lang=None, is_link=False):
        r"""Build the path to a certain kind of page.

        These are mostly defined by plugins by registering via the
        register_path_handler method, except for slug, post_path, root
        and filename which are defined in this class' init method.

        Here's some of the others, for historical reasons:

        * root (name is ignored)
        * tag_index (name is ignored)
        * tag (and name is the tag name)
        * tag_rss (name is the tag name)
        * category (and name is the category name)
        * category_rss (and name is the category name)
        * archive (and name is the year, or None for the main archive index)
        * index (name is the number in index-number)
        * rss (name is ignored)
        * gallery (name is the gallery name)
        * listing (name is the source code file name)
        * post_path (name is 1st element in a POSTS/PAGES tuple)
        * slug (name is the slug of a post or page)
        * filename (name is the source filename of a post/page, in DEFAULT_LANG, relative to conf.py)

        The returned value is always a path relative to output, like
        "categories/whatever.html"

        If is_link is True, the path is absolute and uses "/" as separator
        (ex: "/archive/index.html").
        If is_link is False, the path is relative to output and uses the
        platform's separator.
        (ex: "archive\index.html")
        """
        if lang is None:
            lang = utils.LocaleBorg().current_lang

        try:
            path = self.path_handlers[kind](name, lang)
            path = [os.path.normpath(p) for p in path if p != '.']  # Fix Issue #1028
            if is_link:
                link = '/' + ('/'.join(path))
                index_len = len(self.config['INDEX_FILE'])
                if self.config['STRIP_INDEXES'] and \
                        link[-(1 + index_len):] == '/' + self.config['INDEX_FILE']:
                    return link[:-index_len]
                else:
                    return link
            else:
                return os.path.join(*path)
        except KeyError:
            utils.LOGGER.warn("Unknown path request of kind: {0}".format(kind))
            return ""

    def post_path(self, name, lang):
        """Link to the destination of an element in the POSTS/PAGES settings.

        Example:

        link://post_path/posts => /blog
        """
        return [_f for _f in [self.config['TRANSLATIONS'][lang],
                              os.path.dirname(name),
                              self.config['INDEX_FILE']] if _f]

    def root_path(self, name, lang):
        """Link to the current language's root.

        Example:

        link://root_path => /

        link://root_path => /translations/spanish/
        """
        d = self.config['TRANSLATIONS'][lang]
        if d:
            return [d, '']
        else:
            return []

    def slug_path(self, name, lang):
        """A link to a post with given slug, if not ambiguous.

        Example:

        link://slug/yellow-camaro => /posts/cars/awful/yellow-camaro/index.html
        """
        results = [p for p in self.timeline if p.meta('slug') == name]
        if not results:
            utils.LOGGER.warning("Cannot resolve path request for slug: {0}".format(name))
        else:
            if len(results) > 1:
                utils.LOGGER.warning('Ambiguous path request for slug: {0}'.format(name))
            return [_f for _f in results[0].permalink(lang).split('/') if _f]

    def filename_path(self, name, lang):
        """Link to post or page by source filename.

        Example:

        link://filename/manual.txt => /docs/handbook.html
        """
        results = [p for p in self.timeline if p.source_path == name]
        if not results:
            utils.LOGGER.warning("Cannot resolve path request for filename: {0}".format(name))
        else:
            if len(results) > 1:
                utils.LOGGER.error("Ambiguous path request for filename: {0}".format(name))
            return [_f for _f in results[0].permalink(lang).split('/') if _f]

    def register_path_handler(self, kind, f):
        """Register a path handler."""
        if kind in self.path_handlers:
            utils.LOGGER.warning('Conflicting path handlers for kind: {0}'.format(kind))
        else:
            self.path_handlers[kind] = f

    def link(self, *args):
        """Create a link."""
        url = self.path(*args, is_link=True)
        url = utils.encodelink(url)
        return url

    def abs_link(self, dst, protocol_relative=False):
        """Get an absolute link."""
        # Normalize
        if dst:  # Mako templates and empty strings evaluate to False
            dst = urljoin(self.config['BASE_URL'], dst.lstrip('/'))
        else:
            dst = self.config['BASE_URL']
        url = urlparse(dst).geturl()
        if protocol_relative:
            url = url.split(":", 1)[1]
        url = utils.encodelink(url)
        return url

    def rel_link(self, src, dst):
        """Get a relative link."""
        # Normalize
        src = urljoin(self.config['BASE_URL'], src)
        dst = urljoin(src, dst)
        # Avoid empty links.
        if src == dst:
            return "#"
        # Check that link can be made relative, otherwise return dest
        parsed_src = urlsplit(src)
        parsed_dst = urlsplit(dst)
        if parsed_src[:2] != parsed_dst[:2]:
            return utils.encodelink(dst)
        # Now both paths are on the same site and absolute
        src_elems = parsed_src.path.split('/')[1:]
        dst_elems = parsed_dst.path.split('/')[1:]
        i = 0
        for (i, s), d in zip(enumerate(src_elems), dst_elems):
            if s != d:
                break
        else:
            i += 1
        # Now i is the longest common prefix
        url = '/'.join(['..'] * (len(src_elems) - i - 1) + dst_elems[i:])
        url = utils.encodelink(url)
        return url

    def file_exists(self, path, not_empty=False):
        """Check if the file exists. If not_empty is True, it also must not be empty."""
        exists = os.path.exists(path)
        if exists and not_empty:
            exists = os.stat(path).st_size > 0
        return exists

    def clean_task_paths(self, task):
        """Normalize target paths in the task."""
        targets = task.get('targets', None)
        if targets is not None:
            task['targets'] = [os.path.normpath(t) for t in targets]
        return task

    def gen_tasks(self, name, plugin_category, doc=''):
        """Generate tasks."""
        def flatten(task):
            """Flatten lists of tasks."""
            if isinstance(task, dict):
                yield task
            else:
                for t in task:
                    for ft in flatten(t):
                        yield ft

        task_dep = []
        for pluginInfo in self.plugin_manager.getPluginsOfCategory(plugin_category):
            for task in flatten(pluginInfo.plugin_object.gen_tasks()):
                assert 'basename' in task
                task = self.clean_task_paths(task)
                if 'task_dep' not in task:
                    task['task_dep'] = []
                task['task_dep'].extend(self.injected_deps[task['basename']])
                yield task
                for multi in self.plugin_manager.getPluginsOfCategory("TaskMultiplier"):
                    flag = False
                    for task in multi.plugin_object.process(task, name):
                        flag = True
                        yield self.clean_task_paths(task)
                    if flag:
                        task_dep.append('{0}_{1}'.format(name, multi.plugin_object.name))
            if pluginInfo.plugin_object.is_default:
                task_dep.append(pluginInfo.plugin_object.name)
        yield {
            'basename': name,
            'doc': doc,
            'actions': None,
            'clean': True,
            'task_dep': task_dep
        }

    def parse_category_name(self, category_name):
        """Parse a category name into a hierarchy."""
        if self.config['CATEGORY_ALLOW_HIERARCHIES']:
            try:
                return utils.parse_escaped_hierarchical_category_name(category_name)
            except Exception as e:
                utils.LOGGER.error(str(e))
                sys.exit(1)
        else:
            return [category_name] if len(category_name) > 0 else []

    def category_path_to_category_name(self, category_path):
        """Translate a category path to a category name."""
        if self.config['CATEGORY_ALLOW_HIERARCHIES']:
            return utils.join_hierarchical_category_path(category_path)
        else:
            return ''.join(category_path)

    def _add_post_to_category(self, post, category_name):
        """Add a post to a category."""
        category_path = self.parse_category_name(category_name)
        current_path = []
        current_subtree = self.category_hierarchy
        for current in category_path:
            current_path.append(current)
            if current not in current_subtree:
                current_subtree[current] = {}
            current_subtree = current_subtree[current]
            self.posts_per_category[self.category_path_to_category_name(current_path)].append(post)

    def _sort_category_hierarchy(self):
        """Sort category hierarchy."""
        # First create a hierarchy of TreeNodes
        self.category_hierarchy_lookup = {}

        def create_hierarchy(cat_hierarchy, parent=None):
            """Create category hierarchy."""
            result = []
            for name, children in cat_hierarchy.items():
                node = utils.TreeNode(name, parent)
                node.children = create_hierarchy(children, node)
                node.category_path = [pn.name for pn in node.get_path()]
                node.category_name = self.category_path_to_category_name(node.category_path)
                self.category_hierarchy_lookup[node.category_name] = node
                if node.category_name not in self.config.get('HIDDEN_CATEGORIES'):
                    result.append(node)
            return natsort.natsorted(result, key=lambda e: e.name, alg=natsort.ns.F | natsort.ns.IC)

        root_list = create_hierarchy(self.category_hierarchy)
        # Next, flatten the hierarchy
        self.category_hierarchy = utils.flatten_tree_structure(root_list)

    def scan_posts(self, really=False, ignore_quit=False, quiet=False):
        """Scan all the posts.

        The `quiet` option is ignored.
        """
        if self._scanned and not really:
            return

        # Reset things
        self.posts = []
        self.all_posts = []
        self.posts_per_year = defaultdict(list)
        self.posts_per_month = defaultdict(list)
        self.posts_per_tag = defaultdict(list)
        self.posts_per_category = defaultdict(list)
        self.tags_per_language = defaultdict(list)
        self.category_hierarchy = {}
        self.post_per_file = {}
        self.post_per_input_file = {}
        self.timeline = []
        self.pages = []

        for p in self.plugin_manager.getPluginsOfCategory('PostScanner'):
            timeline = p.plugin_object.scan()
            # FIXME: can there be conflicts here?
            self.timeline.extend(timeline)

        quit = False
        # Classify posts per year/tag/month/whatever
        slugged_tags = defaultdict(set)
        for post in self.timeline:
            if post.use_in_feeds:
                self.posts.append(post)
                self.posts_per_year[str(post.date.year)].append(post)
                self.posts_per_month[
                    '{0}/{1:02d}'.format(post.date.year, post.date.month)].append(post)
                for lang in self.config['TRANSLATIONS'].keys():
                    for tag in post.tags_for_language(lang):
                        _tag_slugified = utils.slugify(tag, lang)
                        if _tag_slugified in slugged_tags[lang]:
                            if tag not in self.posts_per_tag:
                                # Tags that differ only in case
                                other_tag = [existing for existing in self.posts_per_tag.keys() if utils.slugify(existing, lang) == _tag_slugified][0]
                                utils.LOGGER.error('You have tags that are too similar: {0} and {1}'.format(tag, other_tag))
                                utils.LOGGER.error('Tag {0} is used in: {1}'.format(tag, post.source_path))
                                utils.LOGGER.error('Tag {0} is used in: {1}'.format(other_tag, ', '.join([p.source_path for p in self.posts_per_tag[other_tag]])))
                                quit = True
                        else:
                            slugged_tags[lang].add(_tag_slugified)
                        if post not in self.posts_per_tag[tag]:
                            self.posts_per_tag[tag].append(post)
                    self.tags_per_language[lang].extend(post.tags_for_language(lang))
                self._add_post_to_category(post, post.meta('category'))

            if post.is_post:
                # unpublished posts
                self.all_posts.append(post)
            else:
                self.pages.append(post)

            for lang in self.config['TRANSLATIONS'].keys():
                dest = post.destination_path(lang=lang)
                src_dest = post.destination_path(lang=lang, extension=post.source_ext())
                src_file = post.translated_source_path(lang=lang)
                if dest in self.post_per_file:
                    utils.LOGGER.error('Two posts are trying to generate {0}: {1} and {2}'.format(
                        dest,
                        self.post_per_file[dest].source_path,
                        post.source_path))
                    quit = True
                if (src_dest in self.post_per_file) and self.config['COPY_SOURCES']:
                    utils.LOGGER.error('Two posts are trying to generate {0}: {1} and {2}'.format(
                        src_dest,
                        self.post_per_file[dest].source_path,
                        post.source_path))
                    quit = True
                self.post_per_file[dest] = post
                self.post_per_file[src_dest] = post
                self.post_per_input_file[src_file] = post
                # deduplicate tags_per_language
                self.tags_per_language[lang] = list(set(self.tags_per_language[lang]))

        # Sort everything.

        for thing in self.timeline, self.posts, self.all_posts, self.pages:
            thing.sort(key=lambda p:
                       (int(p.meta('priority')) if p.meta('priority') else 0,
                        p.date, p.source_path))
            thing.reverse()
        self._sort_category_hierarchy()

        for i, p in enumerate(self.posts[1:]):
            p.next_post = self.posts[i]
        for i, p in enumerate(self.posts[:-1]):
            p.prev_post = self.posts[i + 1]
        self._scanned = True
        if not self.quiet:
            print("done!", file=sys.stderr)
        if quit and not ignore_quit:
            sys.exit(1)
        signal('scanned').send(self)

    def generic_renderer(self, lang, output_name, template_name, filters, file_deps=None, uptodate_deps=None, context=None, context_deps_remove=None, post_deps_dict=None, url_type=None):
        """Helper function for rendering pages and post lists and other related pages.

        lang is the current language.
        output_name is the destination file name.
        template_name is the template to be used.
        filters is the list of filters (usually site.config['FILTERS']) which will be used to post-process the result.
        file_deps (optional) is a list of additional file dependencies (next to template and its dependencies).
        uptodate_deps (optional) is a list of additional entries added to the task's uptodate list.
        context (optional) a dict used as a basis for the template context. The lang parameter will always be added.
        context_deps_remove (optional) is a list of keys to remove from the context after using it as an uptodate dependency. This should name all keys containing non-trivial Python objects; they can be replaced by adding JSON-style dicts in post_deps_dict.
        post_deps_dict (optional) is a dict merged into the copy of context which is used as an uptodate dependency.
        url_type (optional) allows to override the ``URL_TYPE`` configuration
        """
        utils.LocaleBorg().set_locale(lang)

        file_deps = copy(file_deps) if file_deps else []
        file_deps += self.template_system.template_deps(template_name)
        file_deps = sorted(list(filter(None, file_deps)))

        context = copy(context) if context else {}
        context["lang"] = lang

        deps_dict = copy(context)
        if context_deps_remove:
            for key in context_deps_remove:
                deps_dict.pop(key)
        deps_dict['OUTPUT_FOLDER'] = self.config['OUTPUT_FOLDER']
        deps_dict['TRANSLATIONS'] = self.config['TRANSLATIONS']
        deps_dict['global'] = self.GLOBAL_CONTEXT
        if post_deps_dict:
            deps_dict.update(post_deps_dict)

        for k, v in self.GLOBAL_CONTEXT['template_hooks'].items():
            deps_dict['||template_hooks|{0}||'.format(k)] = v._items

        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            deps_dict[k] = deps_dict['global'][k](lang)

        deps_dict['navigation_links'] = deps_dict['global']['navigation_links'](lang)

        task = {
            'name': os.path.normpath(output_name),
            'targets': [output_name],
            'file_dep': file_deps,
            'actions': [(self.render_template, [template_name, output_name,
                                                context, url_type])],
            'clean': True,
            'uptodate': [config_changed(deps_dict, 'nikola.nikola.Nikola.generic_renderer')] + ([] if uptodate_deps is None else uptodate_deps)
        }

        return utils.apply_filters(task, filters)

    def generic_page_renderer(self, lang, post, filters, context=None):
        """Render post fragments to final HTML pages."""
        extension = self.get_compiler(post.source_path).extension()
        output_name = os.path.join(self.config['OUTPUT_FOLDER'],
                                   post.destination_path(lang, extension))

        deps = post.deps(lang)
        uptodate_deps = post.deps_uptodate(lang)
        deps.extend(utils.get_asset_path(x, self.THEMES) for x in ('bundles', 'parent', 'engine'))

        context = copy(context) if context else {}
        context['post'] = post
        context['title'] = post.title(lang)
        context['description'] = post.description(lang)
        context['permalink'] = post.permalink(lang)
        if 'pagekind' not in context:
            context['pagekind'] = ['generic_page']
        if post.use_in_feeds:
            context['enable_comments'] = True
        else:
            context['enable_comments'] = self.config['COMMENTS_IN_PAGES']

        deps_dict = {}
        if post.prev_post:
            deps_dict['PREV_LINK'] = [post.prev_post.permalink(lang)]
        if post.next_post:
            deps_dict['NEXT_LINK'] = [post.next_post.permalink(lang)]
        deps_dict['comments'] = context['enable_comments']
        if post:
            deps_dict['post_translations'] = post.translated_to

        yield self.generic_renderer(lang, output_name, post.template_name, filters,
                                    file_deps=deps,
                                    uptodate_deps=uptodate_deps,
                                    context=context,
                                    context_deps_remove=['post'],
                                    post_deps_dict=deps_dict)

    def generic_post_list_renderer(self, lang, posts, output_name, template_name, filters, extra_context):
        """Render pages with lists of posts."""
        deps = []
        uptodate_deps = []
        for post in posts:
            deps += post.deps(lang)
            uptodate_deps += post.deps_uptodate(lang)

        context = {}
        context["posts"] = posts
        context["title"] = self.config['BLOG_TITLE'](lang)
        context["description"] = self.config['BLOG_DESCRIPTION'](lang)
        context["prevlink"] = None
        context["nextlink"] = None
        if extra_context:
            context.update(extra_context)

        post_deps_dict = {}
        post_deps_dict["posts"] = [(p.meta[lang]['title'], p.permalink(lang)) for p in posts]

        return self.generic_renderer(lang, output_name, template_name, filters,
                                     file_deps=deps,
                                     uptodate_deps=uptodate_deps,
                                     context=context,
                                     post_deps_dict=post_deps_dict)

    def atom_feed_renderer(self, lang, posts, output_path, filters,
                           extra_context):
        """Render Atom feeds and archives with lists of posts.

        Feeds are considered archives when no future updates to them are expected.
        """
        def atom_link(link_rel, link_type, link_href):
            link = lxml.etree.Element("link")
            link.set("rel", link_rel)
            link.set("type", link_type)
            link.set("href", utils.encodelink(link_href))
            return link

        utils.LocaleBorg().set_locale(lang)
        deps = []
        uptodate_deps = []
        for post in posts:
            deps += post.deps(lang)
            uptodate_deps += post.deps_uptodate(lang)
        context = {}
        context["posts"] = posts
        context["title"] = self.config['BLOG_TITLE'](lang)
        context["description"] = self.config['BLOG_DESCRIPTION'](lang)
        context["lang"] = lang
        context["prevlink"] = None
        context["nextlink"] = None
        context["is_feed_stale"] = None
        context.update(extra_context)
        deps_context = copy(context)
        deps_context["posts"] = [(p.meta[lang]['title'], p.permalink(lang)) for p in
                                 posts]
        deps_context["global"] = self.GLOBAL_CONTEXT

        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            deps_context[k] = deps_context['global'][k](lang)

        deps_context['navigation_links'] = deps_context['global']['navigation_links'](lang)

        nslist = {}
        if context["is_feed_stale"] or "feedpagenum" in context and (not context["feedpagenum"] == context["feedpagecount"] - 1 and not context["feedpagenum"] == 0):
            nslist["fh"] = "http://purl.org/syndication/history/1.0"
        feed_xsl_link = self.abs_link("/assets/xml/atom.xsl")
        feed_root = lxml.etree.Element("feed", nsmap=nslist)
        feed_root.addprevious(lxml.etree.ProcessingInstruction(
            "xml-stylesheet",
            'href="' + utils.encodelink(feed_xsl_link) + '" type="text/xsl media="all"'))
        feed_root.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
        feed_root.set("xmlns", "http://www.w3.org/2005/Atom")
        feed_title = lxml.etree.SubElement(feed_root, "title")
        feed_title.text = context["title"]
        feed_id = lxml.etree.SubElement(feed_root, "id")
        feed_id.text = self.abs_link(context["feedlink"])
        feed_updated = lxml.etree.SubElement(feed_root, "updated")
        feed_updated.text = utils.LocaleBorg().formatted_date('webiso', datetime.datetime.now(tz=dateutil.tz.tzutc()))
        feed_author = lxml.etree.SubElement(feed_root, "author")
        feed_author_name = lxml.etree.SubElement(feed_author, "name")
        feed_author_name.text = self.config["BLOG_AUTHOR"](lang)
        feed_root.append(atom_link("self", "application/atom+xml",
                                   self.abs_link(context["feedlink"])))
        # Older is "next" and newer is "previous" in paginated feeds (opposite of archived)
        if "nextfeedlink" in context:
            feed_root.append(atom_link("next", "application/atom+xml",
                                       self.abs_link(context["nextfeedlink"])))
        if "prevfeedlink" in context:
            feed_root.append(atom_link("previous", "application/atom+xml",
                                       self.abs_link(context["prevfeedlink"])))
        if context["is_feed_stale"] or "feedpagenum" in context and not context["feedpagenum"] == 0:
            feed_root.append(atom_link("current", "application/atom+xml",
                             self.abs_link(context["currentfeedlink"])))
            # Older is "prev-archive" and newer is "next-archive" in archived feeds (opposite of paginated)
            if "prevfeedlink" in context and (context["is_feed_stale"] or "feedpagenum" in context and not context["feedpagenum"] == context["feedpagecount"] - 1):
                feed_root.append(atom_link("next-archive", "application/atom+xml",
                                           self.abs_link(context["prevfeedlink"])))
            if "nextfeedlink" in context:
                feed_root.append(atom_link("prev-archive", "application/atom+xml",
                                           self.abs_link(context["nextfeedlink"])))
            if context["is_feed_stale"] or "feedpagenum" and not context["feedpagenum"] == context["feedpagecount"] - 1:
                lxml.etree.SubElement(feed_root, "{http://purl.org/syndication/history/1.0}archive")
        feed_root.append(atom_link("alternate", "text/html",
                                   self.abs_link(context["permalink"])))
        feed_generator = lxml.etree.SubElement(feed_root, "generator")
        feed_generator.set("uri", "https://getnikola.com/")
        feed_generator.text = "Nikola"

        feed_append_query = None
        if self.config["FEED_LINKS_APPEND_QUERY"]:
            feed_append_query = self.config["FEED_LINKS_APPEND_QUERY"].format(
                feedRelUri=context["feedlink"],
                feedFormat="atom")

        def atom_post_text(post, text):
            if not self.config["FEED_PLAIN"]:
                if self.config["FEED_PREVIEWIMAGE"] and 'previewimage' in post.meta[lang] and post.meta[lang]['previewimage'] not in text:
                    text = "<figure><img src=\"{}\"></figure> {}".format(post.meta[lang]['previewimage'], text)

                # FIXME: this is duplicated with code in Post.text() and generic_rss_renderer
                try:
                    doc = lxml.html.document_fromstring(text)
                    doc.rewrite_links(lambda dst: self.url_replacer(post.permalink(lang), dst, lang, 'absolute'))
                    try:
                        body = doc.body
                        text = (body.text or '') + ''.join(
                            [lxml.html.tostring(child, encoding='unicode')
                                for child in body.iterchildren()])
                    except IndexError:  # No body there, it happens sometimes
                        text = ''
                except lxml.etree.ParserError as e:
                    if str(e) == "Document is empty":
                        text = ""
                    else:  # let other errors raise
                        raise(e)
            return text.strip()

        for post in posts:
            summary = atom_post_text(post, post.text(lang, teaser_only=True,
                                                     strip_html=self.config["FEED_PLAIN"],
                                                     feed_read_more_link=True,
                                                     feed_links_append_query=feed_append_query))
            content = None
            if not self.config["FEED_TEASERS"]:
                content = atom_post_text(post, post.text(lang, teaser_only=self.config["FEED_TEASERS"],
                                                         strip_html=self.config["FEED_PLAIN"],
                                                         feed_read_more_link=True,
                                                         feed_links_append_query=feed_append_query))

            entry_root = lxml.etree.SubElement(feed_root, "entry")
            entry_title = lxml.etree.SubElement(entry_root, "title")
            entry_title.text = post.title(lang)
            entry_id = lxml.etree.SubElement(entry_root, "id")
            entry_id.text = post.permalink(lang, absolute=True)
            entry_updated = lxml.etree.SubElement(entry_root, "updated")
            entry_updated.text = post.formatted_updated('webiso')
            entry_published = lxml.etree.SubElement(entry_root, "published")
            entry_published.text = post.formatted_date('webiso')
            entry_author = lxml.etree.SubElement(entry_root, "author")
            entry_author_name = lxml.etree.SubElement(entry_author, "name")
            entry_author_name.text = post.author(lang)
            entry_root.append(atom_link("alternate", "text/html",
                              post.permalink(lang, absolute=True,
                                             query=feed_append_query)))
            entry_summary = lxml.etree.SubElement(entry_root, "summary")
            if not self.config["FEED_PLAIN"]:
                entry_summary.set("type", "html")
            else:
                entry_summary.set("type", "text")
            entry_summary.text = summary
            if content:
                entry_content = lxml.etree.SubElement(entry_root, "content")
                if not self.config["FEED_PLAIN"]:
                    entry_content.set("type", "html")
                else:
                    entry_content.set("type", "text")
                entry_content.text = content
            for category in post.tags_for_language(lang):
                entry_category = lxml.etree.SubElement(entry_root, "category")
                entry_category.set("term", utils.slugify(category, lang))
                entry_category.set("label", category)

        dst_dir = os.path.dirname(output_path)
        utils.makedirs(dst_dir)
        with io.open(output_path, "w+", encoding="utf-8") as atom_file:
            data = lxml.etree.tostring(feed_root.getroottree(), encoding="UTF-8", pretty_print=True, xml_declaration=True)
            if isinstance(data, utils.bytes_str):
                data = data.decode('utf-8')
            atom_file.write(data)

    def generic_index_renderer(self, lang, posts, indexes_title, template_name, context_source, kw, basename, page_link, page_path, additional_dependencies=[]):
        """Create an index page.

        lang: The language
        posts: A list of posts
        indexes_title: Title
        template_name: Name of template file
        context_source: This will be copied and extended and used as every
                        page's context
        kw: An extended version will be used for uptodate dependencies
        basename: Basename for task
        page_link: A function accepting an index i, the displayed page number,
                   the number of pages, and a boolean force_addition
                   which creates a link to the i-th page (where i ranges
                   between 0 and num_pages-1). The displayed page (between 1
                   and num_pages) is the number (optionally) displayed as
                   'page %d' on the rendered page. If force_addition is True,
                   the appendum (inserting '-%d' etc.) should be done also for
                   i == 0.
        page_path: A function accepting an index i, the displayed page number,
                   the number of pages, and a boolean force_addition,
                   which creates a path to the i-th page. All arguments are
                   as the ones for page_link.
        additional_dependencies: a list of dependencies which will be added
                                 to task['uptodate']
        """
        # Update kw
        kw = kw.copy()
        kw["tag_pages_are_indexes"] = self.config['TAG_PAGES_ARE_INDEXES']
        kw["index_display_post_count"] = self.config['INDEX_DISPLAY_POST_COUNT']
        kw["index_teasers"] = self.config['INDEX_TEASERS']
        kw["indexes_pages"] = self.config['INDEXES_PAGES'](lang)
        kw["indexes_pages_main"] = self.config['INDEXES_PAGES_MAIN']
        kw["indexes_static"] = self.config['INDEXES_STATIC']
        kw['indexes_prety_page_url'] = self.config["INDEXES_PRETTY_PAGE_URL"]
        kw['demote_headers'] = self.config['DEMOTE_HEADERS']
        kw['generate_atom'] = self.config["GENERATE_ATOM"]
        kw['feed_link_append_query'] = self.config["FEED_LINKS_APPEND_QUERY"]
        kw['currentfeed'] = None

        # Split in smaller lists
        lists = []
        if kw["indexes_static"]:
            lists.append(posts[:kw["index_display_post_count"]])
            posts = posts[kw["index_display_post_count"]:]
            while posts:
                lists.append(posts[-kw["index_display_post_count"]:])
                posts = posts[:-kw["index_display_post_count"]]
        else:
            while posts:
                lists.append(posts[:kw["index_display_post_count"]])
                posts = posts[kw["index_display_post_count"]:]
        num_pages = len(lists)
        for i, post_list in enumerate(lists):
            context = context_source.copy()
            if 'pagekind' not in context:
                context['pagekind'] = ['index']
            ipages_i = utils.get_displayed_page_number(i, num_pages, self)
            if kw["indexes_pages"]:
                indexes_pages = kw["indexes_pages"] % ipages_i
            else:
                if kw["indexes_pages_main"]:
                    ipages_msg = "page %d"
                else:
                    ipages_msg = "old posts, page %d"
                indexes_pages = " (" + \
                    kw["messages"][lang][ipages_msg] % ipages_i + ")"
            if i > 0 or kw["indexes_pages_main"]:
                context["title"] = indexes_title + indexes_pages
            else:
                context["title"] = indexes_title
            context["prevlink"] = None
            context["nextlink"] = None
            context['index_teasers'] = kw['index_teasers']
            prevlink = None
            nextlink = None
            if kw["indexes_static"]:
                if i > 0:
                    if i < num_pages - 1:
                        prevlink = i + 1
                    elif i == num_pages - 1:
                        prevlink = 0
                if num_pages > 1:
                    if i > 1:
                        nextlink = i - 1
                    elif i == 0:
                        nextlink = num_pages - 1
            else:
                if i >= 1:
                    prevlink = i - 1
                if i < num_pages - 1:
                    nextlink = i + 1
            if prevlink is not None:
                context["prevlink"] = page_link(prevlink,
                                                utils.get_displayed_page_number(prevlink, num_pages, self),
                                                num_pages, False)
                context["prevfeedlink"] = page_link(prevlink,
                                                    utils.get_displayed_page_number(prevlink, num_pages, self),
                                                    num_pages, False, extension=".atom")
            if nextlink is not None:
                context["nextlink"] = page_link(nextlink,
                                                utils.get_displayed_page_number(nextlink, num_pages, self),
                                                num_pages, False)
                context["nextfeedlink"] = page_link(nextlink,
                                                    utils.get_displayed_page_number(nextlink, num_pages, self),
                                                    num_pages, False, extension=".atom")
            context["permalink"] = page_link(i, ipages_i, num_pages, False)
            output_name = os.path.join(kw['output_folder'], page_path(i, ipages_i, num_pages, False))
            task = self.generic_post_list_renderer(
                lang,
                post_list,
                output_name,
                template_name,
                kw['filters'],
                context,
            )
            task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.nikola.Nikola.generic_index_renderer')] + additional_dependencies
            task['basename'] = basename
            yield task

            if kw['generate_atom']:
                atom_output_name = os.path.join(kw['output_folder'], page_path(i, ipages_i, num_pages, False, extension=".atom"))
                context["feedlink"] = page_link(i, ipages_i, num_pages, False, extension=".atom")
                if not kw["currentfeed"]:
                    kw["currentfeed"] = context["feedlink"]
                context["currentfeedlink"] = kw["currentfeed"]
                context["feedpagenum"] = i
                context["feedpagecount"] = num_pages
                kw['feed_teasers'] = self.config['FEED_TEASERS']
                kw['feed_plain'] = self.config['FEED_PLAIN']
                kw['feed_previewimage'] = self.config['FEED_PREVIEWIMAGE']
                atom_task = {
                    "basename": basename,
                    "name": atom_output_name,
                    "file_dep": sorted([_.base_path for _ in post_list]),
                    "task_dep": ['render_posts'],
                    "targets": [atom_output_name],
                    "actions": [(self.atom_feed_renderer,
                                (lang,
                                 post_list,
                                 atom_output_name,
                                 kw['filters'],
                                 context,))],
                    "clean": True,
                    "uptodate": [utils.config_changed(kw, 'nikola.nikola.Nikola.atom_feed_renderer')] + additional_dependencies
                }
                yield utils.apply_filters(atom_task, kw['filters'])

        if kw["indexes_pages_main"] and kw['indexes_prety_page_url'](lang):
            # create redirection
            output_name = os.path.join(kw['output_folder'], page_path(0, utils.get_displayed_page_number(0, num_pages, self), num_pages, True))
            link = page_link(0, utils.get_displayed_page_number(0, num_pages, self), num_pages, False)
            yield utils.apply_filters({
                'basename': basename,
                'name': output_name,
                'targets': [output_name],
                'actions': [(utils.create_redirect, (output_name, link))],
                'clean': True,
                'uptodate': [utils.config_changed(kw, 'nikola.nikola.Nikola.generic_index_renderer')],
            }, kw["filters"])

    def __repr__(self):
        """Representation of a Nikola site."""
        return '<Nikola Site: {0!r}>'.format(self.config['BLOG_TITLE'](self.config['DEFAULT_LANG']))


def sanitized_locales(locale_fallback, locale_default, locales, translations):
    """Sanitize all locales availble in Nikola.

    There will be one locale for each language in translations.

    Locales for languages not in translations are ignored.

    An explicit locale for a language can be specified in locales[language].

    Locales at the input must be in the string style (like 'en', 'en.utf8'), and
    the string can be unicode or bytes; at the output will be of type str, as
    required by locale.setlocale.

    Explicit but invalid locales are replaced with the sanitized locale_fallback

    Languages with no explicit locale are set to
        the sanitized locale_default if it was explicitly set
        sanitized guesses compatible with v 6.0.4 if locale_default was None

    NOTE: never use locale.getlocale() , it can return values that
    locale.setlocale will not accept in Windows XP, 7 and pythons 2.6, 2.7, 3.3
    Examples: "Spanish", "French" can't do the full circle set / get / set
    """
    if sys.platform != 'win32':
        workaround_empty_LC_ALL_posix()

    # locales for languages not in translations are ignored
    extras = set(locales) - set(translations)
    if extras:
        msg = 'Unexpected languages in LOCALES, ignoring them: {0}'
        utils.LOGGER.warn(msg.format(', '.join(extras)))
        for lang in extras:
            del locales[lang]

    # py2x: get/setlocale related functions require the locale string as a str
    # so convert
    locale_fallback = str(locale_fallback) if locale_fallback else None
    locale_default = str(locale_default) if locale_default else None
    for lang in locales:
        locales[lang] = str(locales[lang])

    locale_fallback = valid_locale_fallback(locale_fallback)

    # explicit but invalid locales are replaced with the sanitized locale_fallback
    for lang in locales:
        if not is_valid_locale(locales[lang]):
            msg = 'Locale {0} for language {1} not accepted by python locale.'
            utils.LOGGER.warn(msg.format(locales[lang], lang))
            locales[lang] = locale_fallback

    # languages with no explicit locale
    missing = set(translations) - set(locales)
    if locale_default:
        # are set to the sanitized locale_default if it was explicitly set
        if not is_valid_locale(locale_default):
            msg = 'LOCALE_DEFAULT {0} could not be set, using {1}'
            utils.LOGGER.warn(msg.format(locale_default, locale_fallback))
            locale_default = locale_fallback
        for lang in missing:
            locales[lang] = locale_default
    else:
        # are set to sanitized guesses compatible with v 6.0.4 in Linux-Mac (was broken in Windows)
        if sys.platform == 'win32':
            guess_locale_fom_lang = guess_locale_from_lang_windows
        else:
            guess_locale_fom_lang = guess_locale_from_lang_posix
        for lang in missing:
            locale_n = guess_locale_fom_lang(lang)
            if not locale_n:
                locale_n = locale_fallback
                msg = "Could not guess locale for language {0}, using locale {1}"
                utils.LOGGER.warn(msg.format(lang, locale_n))
                utils.LOGGER.warn("Please fix your OS locale configuration or use the LOCALES option in conf.py to specify your preferred locale.")
                if sys.platform != 'win32':
                    utils.LOGGER.warn("Make sure to use an UTF-8 locale to ensure Unicode support.")
            locales[lang] = locale_n

    return locale_fallback, locale_default, locales


def is_valid_locale(locale_n):
    """Check if locale (type str) is valid."""
    try:
        locale.setlocale(locale.LC_ALL, locale_n)
        return True
    except locale.Error:
        return False


def valid_locale_fallback(desired_locale=None):
    """Provide a default fallback_locale, a string that locale.setlocale will accept.

    If desired_locale is provided must be of type str for py2x compatibility
    """
    # Whenever fallbacks change, adjust test TestHarcodedFallbacksWork
    candidates_windows = [str('English'), str('C')]
    candidates_posix = [str('en_US.UTF-8'), str('C')]
    candidates = candidates_windows if sys.platform == 'win32' else candidates_posix
    if desired_locale:
        candidates = list(candidates)
        candidates.insert(0, desired_locale)
    found_valid = False
    for locale_n in candidates:
        found_valid = is_valid_locale(locale_n)
        if found_valid:
            break
    if not found_valid:
        msg = 'Could not find a valid fallback locale, tried: {0}'
        utils.LOGGER.warn(msg.format(candidates))
    elif desired_locale and (desired_locale != locale_n):
        msg = 'Desired fallback locale {0} could not be set, using: {1}'
        utils.LOGGER.warn(msg.format(desired_locale, locale_n))
    return locale_n


def guess_locale_from_lang_windows(lang):
    """Guess a locale, basing on Windows language."""
    locale_n = str(LEGAL_VALUES['_WINDOWS_LOCALE_GUESSES'].get(lang, None))
    if not is_valid_locale(locale_n):
        locale_n = None
    return locale_n


def guess_locale_from_lang_posix(lang):
    """Guess a locale, basing on POSIX system language."""
    # compatibility v6.0.4
    if is_valid_locale(str(lang)):
        locale_n = str(lang)
    else:
        # this works in Travis when locale support set by Travis suggestion
        locale_n = str((locale.normalize(lang).split('.')[0]) + '.UTF-8')
    if not is_valid_locale(locale_n):
        # http://thread.gmane.org/gmane.comp.web.nikola/337/focus=343
        locale_n = str((locale.normalize(lang).split('.')[0]))
    if not is_valid_locale(locale_n):
        locale_n = None
    return locale_n


def workaround_empty_LC_ALL_posix():
    # clunky hack: we have seen some posix locales with all or most of LC_*
    # defined to the same value, but with LC_ALL empty.
    # Manually doing what we do here seems to work for nikola in that case.
    # It is unknown if it will work when the LC_* aren't homogeneous
    try:
        lc_time = os.environ.get('LC_TIME', None)
        lc_all = os.environ.get('LC_ALL', None)
        if lc_time and not lc_all:
            os.environ['LC_ALL'] = lc_time
    except Exception:
        pass
