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

"""The main Nikola site object."""

import datetime
import io
import json
import functools
import logging
import operator
import os
import pathlib
import sys
import typing
import mimetypes
from collections import defaultdict
from copy import copy
from urllib.parse import urlparse, urlsplit, urlunsplit, urljoin, unquote, parse_qs

import dateutil.tz
import lxml.etree
import lxml.html
import natsort
import PyRSS2Gen as rss
from pkg_resources import resource_filename
from blinker import signal

from . import DEBUG, SHOW_TRACEBACKS, filters, utils, hierarchy_utils, shortcodes
from . import metadata_extractors
from .metadata_extractors import default_metadata_extractors_by
from .post import Post  # NOQA
from .plugin_manager import PluginCandidate, PluginInfo, PluginManager
from .plugin_categories import (
    TemplateSystem,
    PostScanner,
    Taxonomy,
)
from .state import Persistor

try:
    import pyphen
except ImportError:
    pyphen = None

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

# Default "Read more..." link
DEFAULT_INDEX_READ_MORE_LINK = '<p class="more"><a href="{link}">{read_more}…</a></p>'
DEFAULT_FEED_READ_MORE_LINK = '<p><a href="{link}">{read_more}…</a> ({min_remaining_read})</p>'


config_changed = utils.config_changed

__all__ = ('Nikola',)

# We store legal values for some settings here.  For internal use.
LEGAL_VALUES = {
    'DEFAULT_THEME': 'bootblog4',
    'COMMENT_SYSTEM': [
        'disqus',
        'discourse',
        'facebook',
        'intensedebate',
        'isso',
        'muut',
        'commento',
        'utterances',
    ],
    'TRANSLATIONS': {
        'af': 'Afrikaans',
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
        'fur': 'Friulian',
        'gl': 'Galician',
        'he': 'Hebrew',
        'hi': 'Hindi',
        'hr': 'Croatian',
        'hu': 'Hungarian',
        'ia': 'Interlingua',
        'id': 'Indonesian',
        'it': 'Italian',
        ('ja', '!jp'): 'Japanese',
        'ko': 'Korean',
        'lt': 'Lithuanian',
        'mi': 'Maori',
        'ml': 'Malayalam',
        'mr': 'Marathi',
        'nb': 'Norwegian (Bokmål)',
        'nl': 'Dutch',
        'oc': 'Occitan',
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
        'th': 'Thai',
        ('tr', '!tr_TR'): 'Turkish',
        'uk': 'Ukrainian',
        'ur': 'Urdu',
        'vi': 'Vietnamese',
        'zh_cn': 'Chinese (Simplified)',
        'zh_tw': 'Chinese (Traditional)'
    },
    '_TRANSLATIONS_WITH_COUNTRY_SPECIFIERS': {
        # This dict is used in `init` in case of locales that exist with a
        # country specifier.  If there is no other locale that has the same
        # language with a different country, ``nikola init`` (but nobody else!)
        # will accept it, warning the user about it.

        # This dict is currently empty.
    },
    'LOCALES_BASE': {
        # A list of locale mappings to apply for every site. Can be overridden in the config.
        'sr_latin': 'sr_Latn',
    },
    'RTL_LANGUAGES': ('ar', 'fa', 'he', 'ur'),
    'LUXON_LOCALES': defaultdict(lambda: 'en', **{
        'af': 'af',
        'ar': 'ar',
        'az': 'az',
        'bg': 'bg',
        'bn': 'bn',
        'bs': 'bs',
        'ca': 'ca',
        'cs': 'cs',
        'cz': 'cs',
        'da': 'da',
        'de': 'de',
        'el': 'el',
        'en': 'en',
        'eo': 'eo',
        'es': 'es',
        'et': 'et',
        'eu': 'eu',
        'fa': 'fa',
        'fi': 'fi',
        'fr': 'fr',
        'fur': 'fur',
        'gl': 'gl',
        'hi': 'hi',
        'he': 'he',
        'hr': 'hr',
        'hu': 'hu',
        'ia': 'ia',
        'id': 'id',
        'it': 'it',
        'ja': 'ja',
        'ko': 'ko',
        'lt': 'lt',
        'mi': 'mi',
        'ml': 'ml',
        'mr': 'mr',
        'nb': 'nb',
        'nl': 'nl',
        'oc': 'oc',
        'pa': 'pa',
        'pl': 'pl',
        'pt': 'pt',
        'pt_br': 'pt-BR',
        'ru': 'ru',
        'sk': 'sk',
        'sl': 'sl',
        'sq': 'sq',
        'sr': 'sr-Cyrl',
        'sr_latin': 'sr-Latn',
        'sv': 'sv',
        'te': 'te',
        'tr': 'tr',
        'th': 'th',
        'uk': 'uk',
        'ur': 'ur',
        'vi': 'vi',
        'zh_cn': 'zh-CN',
        'zh_tw': 'zh-TW'
    }),
    # TODO: remove in v9
    'MOMENTJS_LOCALES': defaultdict(lambda: 'en', **{
        'af': 'af',
        'ar': 'ar',
        'az': 'az',
        'bg': 'bg',
        'bn': 'bn',
        'bs': 'bs',
        'ca': 'ca',
        'cs': 'cs',
        'cz': 'cs',
        'da': 'da',
        'de': 'de',
        'el': 'el',
        'en': 'en',
        'eo': 'eo',
        'es': 'es',
        'et': 'et',
        'eu': 'eu',
        'fa': 'fa',
        'fi': 'fi',
        'fr': 'fr',
        'gl': 'gl',
        'hi': 'hi',
        'he': 'he',
        'hr': 'hr',
        'hu': 'hu',
        'id': 'id',
        'it': 'it',
        'ja': 'ja',
        'ko': 'ko',
        'lt': 'lt',
        'ml': 'ml',
        'mr': 'mr',
        'nb': 'nb',
        'nl': 'nl',
        'pa': 'pa-in',
        'pl': 'pl',
        'pt': 'pt',
        'pt_br': 'pt-br',
        'ru': 'ru',
        'sk': 'sk',
        'sl': 'sl',
        'sq': 'sq',
        'sr': 'sr-cyrl',
        'sr_latin': 'sr',
        'sv': 'sv',
        'te': 'te',
        'tr': 'tr',
        'th': 'th',
        'uk': 'uk',
        'ur': 'ur',
        'vi': 'vi',
        'zh_cn': 'zh-cn',
        'zh_tw': 'zh-tw'
    }),
    'PYPHEN_LOCALES': {
        'af': 'af',
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
        'af': 'af',
        'ca': 'ca',
        'da': 'da',
        'de': 'de',
        'en': 'en',
        'eo': 'eo',
        'es': 'es',
        'fa': 'fa',
        'fi': 'fi',
        'fr': 'fr',
        'gl': 'gl',
        'he': 'he',
        'it': 'it',
        'ja': 'ja',
        'lt': 'lt',
        'nl': 'nl',
        'pl': 'pl',
        'pt': 'pt_br',  # hope nobody will mind
        'pt_br': 'pt_br',
        'ru': 'ru',
        'sk': 'sk',
        'sv': 'sv',
        'zh_cn': 'zh_cn',
        'zh_tw': 'zh_tw'
    },
    "METADATA_MAPPING": ["yaml", "toml", "rest_docinfo", "markdown_metadata"],
}

# Mapping old pre-taxonomy plugin names to new post-taxonomy plugin names
TAXONOMY_COMPATIBILITY_PLUGIN_NAME_MAP = {
    "render_archive": ["classify_archive"],
    "render_authors": ["classify_authors"],
    "render_indexes": ["classify_page_index", "classify_sections"],  # "classify_indexes" removed from list (see #2591 and special-case logic below)
    "render_tags": ["classify_categories", "classify_tags"],
}

# Default value for the pattern used to name translated files
DEFAULT_TRANSLATIONS_PATTERN = '{path}.{lang}.{ext}'


def _enclosure(post, lang):
    """Add an enclosure to RSS."""
    enclosure = post.meta('enclosure', lang)
    if enclosure:
        try:
            length = int(post.meta('enclosure_length', lang) or 0)
        except KeyError:
            length = 0
        except ValueError:
            utils.LOGGER.warning("Invalid enclosure length for post {0}".format(post.source_path))
            length = 0
        url = enclosure
        mime = mimetypes.guess_type(url)[0]
        return url, length, mime


class Nikola(object):
    """Class that handles site generation.

    Takes a site config as argument on creation.
    """

    plugin_manager: PluginManager
    _template_system: TemplateSystem

    def __init__(self, **config):
        """Initialize proper environment for running tasks."""
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
        self.filters = {}
        self.debug = DEBUG
        self.show_tracebacks = SHOW_TRACEBACKS
        self.colorful = config.pop('__colorful__', False)
        self.invariant = config.pop('__invariant__', False)
        self.quiet = config.pop('__quiet__', False)
        self._doit_config = config.pop('DOIT_CONFIG', {})
        self.original_cwd = config.pop('__cwd__', False)
        self.configuration_filename = config.pop('__configuration_filename__', False)
        self.configured = bool(config)
        self.injected_deps = defaultdict(list)
        self.shortcode_registry = {}
        self.metadata_extractors_by = default_metadata_extractors_by()
        self.registered_auto_watched_folders = set()

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
            'ARCHIVE_PATH': "",
            'ARCHIVE_FILENAME': "archive.html",
            'ARCHIVES_ARE_INDEXES': False,
            'AUTHOR_PATH': 'authors',
            'AUTHOR_PAGES_ARE_INDEXES': False,
            'AUTHOR_PAGES_DESCRIPTIONS': {},
            'AUTHORLIST_MINIMUM_POSTS': 1,
            'BLOG_AUTHOR': 'Default Author',
            'BLOG_TITLE': 'Default Title',
            'BLOG_EMAIL': '',
            'BLOG_DESCRIPTION': 'Default Description',
            'BODY_END': "",
            'CACHE_FOLDER': 'cache',
            'CATEGORIES_INDEX_PATH': '',
            'CATEGORY_PATH': None,  # None means: same as TAG_PATH
            'CATEGORY_PAGES_ARE_INDEXES': None,  # None means: same as TAG_PAGES_ARE_INDEXES
            'CATEGORY_DESCRIPTIONS': {},
            'CATEGORY_TITLES': {},
            'CATEGORY_PREFIX': 'cat_',
            'CATEGORY_ALLOW_HIERARCHIES': False,
            'CATEGORY_OUTPUT_FLAT_HIERARCHY': False,
            'CATEGORY_DESTPATH_AS_DEFAULT': False,
            'CATEGORY_DESTPATH_TRIM_PREFIX': False,
            'CATEGORY_DESTPATH_FIRST_DIRECTORY_ONLY': True,
            'CATEGORY_DESTPATH_NAMES': {},
            'CATEGORY_PAGES_FOLLOW_DESTPATH': False,
            'CATEGORY_TRANSLATIONS': [],
            'CATEGORY_TRANSLATIONS_ADD_DEFAULTS': False,
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
            'RSS_COPYRIGHT': '',
            'RSS_COPYRIGHT_PLAIN': '',
            'RSS_COPYRIGHT_FORMATS': {},
            'COPY_SOURCES': True,
            'CREATE_ARCHIVE_NAVIGATION': False,
            'CREATE_MONTHLY_ARCHIVE': False,
            'CREATE_SINGLE_ARCHIVE': False,
            'CREATE_FULL_ARCHIVES': False,
            'CREATE_DAILY_ARCHIVE': False,
            'DATE_FORMAT': 'yyyy-MM-dd HH:mm',
            'DISABLE_INDEXES': False,
            'DISABLE_MAIN_ATOM_FEED': False,
            'DISABLE_MAIN_RSS_FEED': False,
            'MOMENTJS_DATE_FORMAT': 'YYYY-MM-DD HH:mm',
            'LUXON_DATE_FORMAT': {},
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
            'FILE_METADATA_UNSLUGIFY_TITLES': True,
            'ADDITIONAL_METADATA': {},
            'FILES_FOLDERS': {'files': ''},
            'FILTERS': {},
            'FORCE_ISO8601': False,
            'FRONT_INDEX_HEADER': '',
            'GALLERY_FOLDERS': {'galleries': 'galleries'},
            'GALLERY_SORT_BY_DATE': True,
            'GALLERIES_USE_THUMBNAIL': False,
            'GALLERIES_DEFAULT_THUMBNAIL': None,
            'GLOBAL_CONTEXT_FILLER': [],
            'GZIP_COMMAND': None,
            'GZIP_FILES': False,
            'GZIP_EXTENSIONS': ('.txt', '.htm', '.html', '.css', '.js', '.json', '.xml'),
            'HIDDEN_AUTHORS': [],
            'HIDDEN_TAGS': [],
            'HIDE_REST_DOCINFO': False,
            'HIDDEN_CATEGORIES': [],
            'HYPHENATE': False,
            'IMAGE_FOLDERS': {'images': ''},
            'INDEX_DISPLAY_POST_COUNT': 10,
            'INDEX_FILE': 'index.html',
            'INDEX_TEASERS': False,
            'IMAGE_THUMBNAIL_SIZE': 400,
            'IMAGE_THUMBNAIL_FORMAT': '{name}.thumbnail{ext}',
            'INDEXES_TITLE': "",
            'INDEXES_PAGES': "",
            'INDEXES_PAGES_MAIN': False,
            'INDEXES_PRETTY_PAGE_URL': False,
            'INDEXES_STATIC': True,
            'INDEX_PATH': '',
            'IPYNB_CONFIG': {},
            'KATEX_AUTO_RENDER': '',
            'LICENSE': '',
            'LINK_CHECK_WHITELIST': [],
            'LISTINGS_FOLDERS': {'listings': 'listings'},
            'LOGO_URL': '',
            'DEFAULT_PREVIEW_IMAGE': None,
            'NAVIGATION_LINKS': {},
            'NAVIGATION_ALT_LINKS': {},
            'MARKDOWN_EXTENSIONS': ['fenced_code', 'codehilite', 'extra'],
            'MARKDOWN_EXTENSION_CONFIGS': {},
            'MAX_IMAGE_SIZE': 1280,
            'MATHJAX_CONFIG': '',
            'METADATA_FORMAT': 'nikola',
            'METADATA_MAPPING': {},
            'MULTIPLE_AUTHORS_PER_POST': False,
            'NEW_POST_DATE_PATH': False,
            'NEW_POST_DATE_PATH_FORMAT': '%Y/%m/%d',
            'OLD_THEME_SUPPORT': True,
            'OUTPUT_FOLDER': 'output',
            'POSTS': (("posts/*.txt", "posts", "post.tmpl"),),
            'PRESERVE_EXIF_DATA': False,
            'PRESERVE_ICC_PROFILES': False,
            'PAGES': (("pages/*.txt", "pages", "page.tmpl"),),
            'PANDOC_OPTIONS': [],
            'PRETTY_URLS': True,
            'FUTURE_IS_NOW': False,
            'INDEX_READ_MORE_LINK': DEFAULT_INDEX_READ_MORE_LINK,
            'REDIRECTIONS': [],
            'ROBOTS_EXCLUSIONS': [],
            'GENERATE_ATOM': False,
            'ATOM_EXTENSION': '.atom',
            'ATOM_PATH': '',
            'ATOM_FILENAME_BASE': 'index',
            'FEED_TEASERS': True,
            'FEED_PLAIN': False,
            'FEED_READ_MORE_LINK': DEFAULT_FEED_READ_MORE_LINK,
            'FEED_LINKS_APPEND_QUERY': False,
            'GENERATE_RSS': True,
            'RSS_EXTENSION': '.xml',
            'RSS_LINK': None,
            'RSS_PATH': '',
            'RSS_FILENAME_BASE': 'rss',
            'SEARCH_FORM': '',
            'SHOW_BLOG_TITLE': True,
            'SHOW_INDEX_PAGE_NAVIGATION': False,
            'SHOW_SOURCELINK': True,
            'SHOW_UNTRANSLATED_POSTS': True,
            'SLUG_AUTHOR_PATH': True,
            'SLUG_TAG_PATH': True,
            'SOCIAL_BUTTONS_CODE': '',
            'SITE_URL': 'https://example.com/',
            'PAGE_INDEX': False,
            'SECTION_PATH': '',
            'STRIP_INDEXES': True,
            'TAG_PATH': 'categories',
            'TAG_PAGES_ARE_INDEXES': False,
            'TAG_DESCRIPTIONS': {},
            'TAG_TITLES': {},
            'TAG_TRANSLATIONS': [],
            'TAG_TRANSLATIONS_ADD_DEFAULTS': False,
            'TAGS_INDEX_PATH': '',
            'TAGLIST_MINIMUM_POSTS': 1,
            'TEMPLATE_FILTERS': {},
            'THEME': LEGAL_VALUES['DEFAULT_THEME'],
            'THEME_COLOR': '#5670d4',  # light "corporate blue"
            'THEME_CONFIG': {},
            'THUMBNAIL_SIZE': 180,
            'TRANSLATIONS_PATTERN': DEFAULT_TRANSLATIONS_PATTERN,
            'URL_TYPE': 'rel_path',
            'USE_BUNDLES': True,
            'USE_CDN': False,
            'USE_CDN_WARNING': True,
            'USE_REST_DOCINFO_METADATA': False,
            'USE_FILENAME_AS_TITLE': True,
            'USE_KATEX': False,
            'USE_SLUGIFY': True,
            'USE_TAG_METADATA': True,
            'TIMEZONE': 'UTC',
            'WARN_ABOUT_TAG_METADATA': True,
            'DEPLOY_DRAFTS': True,
            'DEPLOY_FUTURE': False,
            'SCHEDULE_ALL': False,
            'SCHEDULE_RULE': '',
            'DEMOTE_HEADERS': 1,
            'GITHUB_SOURCE_BRANCH': 'master',
            'GITHUB_DEPLOY_BRANCH': 'gh-pages',
            'GITHUB_REMOTE_NAME': 'origin',
            'GITHUB_COMMIT_SOURCE': False,  # WARNING: conf.py.in overrides this with True for backwards compatibility
            'META_GENERATOR_TAG': True,
            'REST_FILE_INSERTION_ENABLED': True,
            'TYPES_TO_HIDE_TITLE': [],
        }

        # set global_context for template rendering
        self._GLOBAL_CONTEXT = {}

        # dependencies for all pages, not included in global context
        self.ALL_PAGE_DEPS = {}

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

        # Use ATOM_PATH when set
        self.config['ATOM_PATH'] = self.config['ATOM_PATH'] or self.config['INDEX_PATH']

        # Make sure we have sane NAVIGATION_LINKS and NAVIGATION_ALT_LINKS.
        if not self.config['NAVIGATION_LINKS']:
            self.config['NAVIGATION_LINKS'] = {self.config['DEFAULT_LANG']: ()}
        if not self.config['NAVIGATION_ALT_LINKS']:
            self.config['NAVIGATION_ALT_LINKS'] = {self.config['DEFAULT_LANG']: ()}

        # Translatability configuration.
        self.config['TRANSLATIONS'] = self.config.get('TRANSLATIONS',
                                                      {self.config['DEFAULT_LANG']: ''})
        for k, v in self.config['TRANSLATIONS'].items():
            if os.path.isabs(v):
                self.config['TRANSLATIONS'][k] = os.path.relpath(v, '/')

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
                                      'NAVIGATION_ALT_LINKS',
                                      'FRONT_INDEX_HEADER',
                                      'INDEX_READ_MORE_LINK',
                                      'FEED_READ_MORE_LINK',
                                      'INDEXES_TITLE',
                                      'CATEGORY_DESTPATH_NAMES',
                                      'CATEGORY_TITLES',
                                      'CATEGORY_DESCRIPTIONS',
                                      'TAG_TITLES',
                                      'TAG_DESCRIPTIONS',
                                      'INDEXES_PAGES',
                                      'INDEXES_PRETTY_PAGE_URL',
                                      'THEME_CONFIG',
                                      # PATH options (Issue #1914)
                                      'ARCHIVE_PATH',
                                      'ARCHIVE_FILENAME',
                                      'TAG_PATH',
                                      'TAGS_INDEX_PATH',
                                      'CATEGORY_PATH',
                                      'CATEGORIES_INDEX_PATH',
                                      'SECTION_PATH',
                                      'INDEX_PATH',
                                      'ATOM_PATH',
                                      'RSS_PATH',
                                      'RSS_FILENAME_BASE',
                                      'ATOM_FILENAME_BASE',
                                      'AUTHOR_PATH',
                                      'DATE_FORMAT',
                                      'LUXON_DATE_FORMAT',
                                      'MOMENTJS_DATE_FORMAT',  # TODO: remove in v9
                                      'RSS_COPYRIGHT',
                                      'RSS_COPYRIGHT_PLAIN',
                                      # Issue #2970
                                      'MARKDOWN_EXTENSION_CONFIGS',
                                      )

        self._GLOBAL_CONTEXT_TRANSLATABLE = ('blog_author',
                                             'blog_title',
                                             'blog_description',
                                             'license',
                                             'content_footer',
                                             'social_buttons_code',
                                             'search_form',
                                             'body_end',
                                             'extra_head_data',
                                             'date_format',
                                             'js_date_format',
                                             'luxon_date_format',
                                             'front_index_header',
                                             'theme_config',
                                             )

        self._ALL_PAGE_DEPS_TRANSLATABLE = ('atom_path',
                                            'rss_path',
                                            'rss_filename_base',
                                            'atom_filename_base',
                                            'index_read_more_link',
                                            'feed_read_more_link',
                                            )
        # WARNING: navigation_(alt_)links SHOULD NOT be added to the list above.
        #          Themes ask for [lang] there and we should provide it.

        # Luxon setup is a dict of dicts, so we need to set up the default here.
        if not self.config['LUXON_DATE_FORMAT']:
            self.config['LUXON_DATE_FORMAT'] = {self.config['DEFAULT_LANG']: {'preset': False, 'format': 'yyyy-MM-dd HH:mm'}}
        # TODO: remove Moment.js stuff in v9
        if 'JS_DATE_FORMAT' in self.config:
            utils.LOGGER.warning("Moment.js was replaced by Luxon in the default themes, which uses different date formats.")
            utils.LOGGER.warning("If you’re using a built-in theme, set LUXON_DATE_FORMAT. If your theme uses Moment.js, you can silence this warning by renaming JS_DATE_FORMAT to MOMENTJS_DATE_FORMAT.")
            utils.LOGGER.warning("Sample Luxon config: LUXON_DATE_FORMAT = " + str(self.config['LUXON_DATE_FORMAT']))
            self.config['MOMENTJS_DATE_FORMAT'] = self.config['LUXON_DATE_FORMAT']

        # We first have to massage MOMENTJS_DATE_FORMAT and LUXON_DATE_FORMAT, otherwise we run into trouble
        if 'MOMENTJS_DATE_FORMAT' in self.config:
            if isinstance(self.config['MOMENTJS_DATE_FORMAT'], dict):
                for k in self.config['MOMENTJS_DATE_FORMAT']:
                    self.config['MOMENTJS_DATE_FORMAT'][k] = json.dumps(self.config['MOMENTJS_DATE_FORMAT'][k])
            else:
                self.config['MOMENTJS_DATE_FORMAT'] = json.dumps(self.config['MOMENTJS_DATE_FORMAT'])

        if 'LUXON_DATE_FORMAT' in self.config:
            for k in self.config['LUXON_DATE_FORMAT']:
                self.config['LUXON_DATE_FORMAT'][k] = json.dumps(self.config['LUXON_DATE_FORMAT'][k])

        for i in self.TRANSLATABLE_SETTINGS:
            try:
                self.config[i] = utils.TranslatableSetting(i, self.config[i], self.config['TRANSLATIONS'])
            except KeyError:
                pass

        # A EXIF_WHITELIST implies you want to keep EXIF data
        if self.config['EXIF_WHITELIST'] and not self.config['PRESERVE_EXIF_DATA']:
            utils.LOGGER.warning('Setting EXIF_WHITELIST implies PRESERVE_EXIF_DATA is set to True')
            self.config['PRESERVE_EXIF_DATA'] = True

        # Setting PRESERVE_EXIF_DATA with an empty EXIF_WHITELIST implies 'keep everything'
        if self.config['PRESERVE_EXIF_DATA'] and not self.config['EXIF_WHITELIST']:
            utils.LOGGER.warning('You are setting PRESERVE_EXIF_DATA and not EXIF_WHITELIST so EXIF data is not really kept.')

        if 'UNSLUGIFY_TITLES' in self.config:
            utils.LOGGER.warning('The UNSLUGIFY_TITLES setting was renamed to FILE_METADATA_UNSLUGIFY_TITLES.')
            self.config['FILE_METADATA_UNSLUGIFY_TITLES'] = self.config['UNSLUGIFY_TITLES']

        if 'TAG_PAGES_TITLES' in self.config:
            utils.LOGGER.warning('The TAG_PAGES_TITLES setting was renamed to TAG_TITLES.')
            self.config['TAG_TITLES'] = self.config['TAG_PAGES_TITLES']

        if 'TAG_PAGES_DESCRIPTIONS' in self.config:
            utils.LOGGER.warning('The TAG_PAGES_DESCRIPTIONS setting was renamed to TAG_DESCRIPTIONS.')
            self.config['TAG_DESCRIPTIONS'] = self.config['TAG_PAGES_DESCRIPTIONS']

        if 'CATEGORY_PAGES_TITLES' in self.config:
            utils.LOGGER.warning('The CATEGORY_PAGES_TITLES setting was renamed to CATEGORY_TITLES.')
            self.config['CATEGORY_TITLES'] = self.config['CATEGORY_PAGES_TITLES']

        if 'CATEGORY_PAGES_DESCRIPTIONS' in self.config:
            utils.LOGGER.warning('The CATEGORY_PAGES_DESCRIPTIONS setting was renamed to CATEGORY_DESCRIPTIONS.')
            self.config['CATEGORY_DESCRIPTIONS'] = self.config['CATEGORY_PAGES_DESCRIPTIONS']

        if 'DISABLE_INDEXES_PLUGIN_INDEX_AND_ATOM_FEED' in self.config:
            utils.LOGGER.warning('The DISABLE_INDEXES_PLUGIN_INDEX_AND_ATOM_FEED setting was renamed and split to DISABLE_INDEXES and DISABLE_MAIN_ATOM_FEED.')
            self.config['DISABLE_INDEXES'] = self.config['DISABLE_INDEXES_PLUGIN_INDEX_AND_ATOM_FEED']
            self.config['DISABLE_MAIN_ATOM_FEED'] = self.config['DISABLE_INDEXES_PLUGIN_INDEX_AND_ATOM_FEED']

        if 'DISABLE_INDEXES_PLUGIN_RSS_FEED' in self.config:
            utils.LOGGER.warning('The DISABLE_INDEXES_PLUGIN_RSS_FEED setting was renamed to DISABLE_MAIN_RSS_FEED.')
            self.config['DISABLE_MAIN_RSS_FEED'] = self.config['DISABLE_INDEXES_PLUGIN_RSS_FEED']

        for val in self.config['DATE_FORMAT'].values.values():
            if '%' in val:
                utils.LOGGER.error('The DATE_FORMAT setting needs to be upgraded.')
                utils.LOGGER.warning("Nikola now uses CLDR-style date strings. http://cldr.unicode.org/translation/date-time-1/date-time")
                utils.LOGGER.warning("Example: %Y-%m-%d %H:%M ==> yyyy-MM-dd HH:mm")
                utils.LOGGER.warning("(note it’s different to what moment.js uses!)")
                sys.exit(1)

        # Silently upgrade LOCALES (remove encoding)
        locales = LEGAL_VALUES['LOCALES_BASE']
        if 'LOCALES' in self.config:
            for k, v in self.config['LOCALES'].items():
                self.config['LOCALES'][k] = v.split('.')[0]
            locales.update(self.config['LOCALES'])
        self.config['LOCALES'] = locales

        if self.config.get('POSTS_SECTIONS'):
            utils.LOGGER.warning("The sections feature has been removed and its functionality has been merged into categories.")
            utils.LOGGER.warning("For more information on how to migrate, please read: https://getnikola.com/blog/upgrading-to-nikola-v8.html#sections-were-replaced-by-categories")

            for section_config_suffix, cat_config_suffix in (
                ('DESCRIPTIONS', 'DESCRIPTIONS'),
                ('TITLE', 'TITLES'),
                ('TRANSLATIONS', 'TRANSLATIONS')
            ):
                section_config = 'POSTS_SECTION_' + section_config_suffix
                cat_config = 'CATEGORY_' + cat_config_suffix
                if section_config in self.config:
                    self.config[section_config].update(self.config[cat_config])
                    self.config[cat_config] = self.config[section_config]

            self.config['CATEGORY_DESTPATH_NAMES'] = self.config.get('POSTS_SECTION_NAME', {})
            # Need to mark this translatable manually.
            self.config['CATEGORY_DESTPATH_NAMES'] = utils.TranslatableSetting('CATEGORY_DESTPATH_NAMES', self.config['CATEGORY_DESTPATH_NAMES'], self.config['TRANSLATIONS'])

            self.config['CATEGORY_DESTPATH_AS_DEFAULT'] = not self.config.get('POSTS_SECTION_FROM_META')
            utils.LOGGER.info("Setting CATEGORY_DESTPATH_AS_DEFAULT = " + str(self.config['CATEGORY_DESTPATH_AS_DEFAULT']))

        if self.config.get('CATEGORY_PAGES_FOLLOW_DESTPATH') and (not self.config.get('CATEGORY_ALLOW_HIERARCHIES') or self.config.get('CATEGORY_OUTPUT_FLAT_HIERARCHY')):
            utils.LOGGER.error('CATEGORY_PAGES_FOLLOW_DESTPATH requires CATEGORY_ALLOW_HIERARCHIES = True, CATEGORY_OUTPUT_FLAT_HIERARCHY = False.')
            sys.exit(1)

        # The Utterances comment system has a required configuration value
        if self.config.get('COMMENT_SYSTEM') == 'utterances':
            utterances_config = self.config.get('GLOBAL_CONTEXT', {}).get('utterances_config', {})
            if not ('issue-term' in utterances_config or 'issue-number' in utterances_config):
                utils.LOGGER.error("COMMENT_SYSTEM = 'utterances' must have either GLOBAL_CONTEXT['utterances_config']['issue-term'] or GLOBAL_CONTEXT['utterances_config']['issue-term'] defined.")

        # Handle CONTENT_FOOTER and RSS_COPYRIGHT* properly.
        # We provide the arguments to format in CONTENT_FOOTER_FORMATS and RSS_COPYRIGHT_FORMATS.
        self.config['CONTENT_FOOTER'].langformat(self.config['CONTENT_FOOTER_FORMATS'])
        self.config['RSS_COPYRIGHT'].langformat(self.config['RSS_COPYRIGHT_FORMATS'])
        self.config['RSS_COPYRIGHT_PLAIN'].langformat(self.config['RSS_COPYRIGHT_FORMATS'])

        # propagate USE_SLUGIFY
        utils.USE_SLUGIFY = self.config['USE_SLUGIFY']

        # Make sure we have pyphen installed if we are using it
        if self.config.get('HYPHENATE') and pyphen is None:
            utils.LOGGER.warning('To use the hyphenation, you have to install '
                                 'the "pyphen" package.')
            utils.LOGGER.warning('Setting HYPHENATE to False.')
            self.config['HYPHENATE'] = False

        # FIXME: Internally, we still use post_pages because it's a pain to change it
        self.config['post_pages'] = []
        for i1, i2, i3 in self.config['POSTS']:
            self.config['post_pages'].append([i1, i2, i3, True])
        for i1, i2, i3 in self.config['PAGES']:
            self.config['post_pages'].append([i1, i2, i3, False])

        # Handle old plugin names (from before merging the taxonomy PR #2535)
        for old_plugin_name, new_plugin_names in TAXONOMY_COMPATIBILITY_PLUGIN_NAME_MAP.items():
            if old_plugin_name in self.config['DISABLED_PLUGINS']:
                missing_plugins = []
                for plugin_name in new_plugin_names:
                    if plugin_name not in self.config['DISABLED_PLUGINS']:
                        missing_plugins.append(plugin_name)
                if missing_plugins:
                    utils.LOGGER.warning('The "{}" plugin was replaced by several taxonomy plugins (see PR #2535): {}'.format(old_plugin_name, ', '.join(new_plugin_names)))
                    utils.LOGGER.warning('You are currently disabling "{}", but not the following new taxonomy plugins: {}'.format(old_plugin_name, ', '.join(missing_plugins)))
                    utils.LOGGER.warning('Please also disable these new plugins or remove "{}" from the DISABLED_PLUGINS list.'.format(old_plugin_name))
                    self.config['DISABLED_PLUGINS'].extend(missing_plugins)

        # Special-case logic for "render_indexes" to fix #2591
        if 'render_indexes' in self.config['DISABLED_PLUGINS']:
            if 'generate_rss' in self.config['DISABLED_PLUGINS'] or self.config['GENERATE_RSS'] is False:
                if 'classify_indexes' not in self.config['DISABLED_PLUGINS']:
                    utils.LOGGER.warning('You are disabling the "render_indexes" plugin, as well as disabling the "generate_rss" plugin or setting GENERATE_RSS to False. To achieve the same effect, please disable the "classify_indexes" plugin in the future.')
                    self.config['DISABLED_PLUGINS'].append('classify_indexes')
            else:
                if not self.config['DISABLE_INDEXES']:
                    utils.LOGGER.warning('You are disabling the "render_indexes" plugin, but not the generation of RSS feeds. Please put "DISABLE_INDEXES = True" into your configuration instead.')
                    self.config['DISABLE_INDEXES'] = True

        # Disable RSS.  For a successful disable, we must have both the option
        # false and the plugin disabled through the official means.
        if 'generate_rss' in self.config['DISABLED_PLUGINS'] and self.config['GENERATE_RSS'] is True:
            utils.LOGGER.warning('Please use GENERATE_RSS to disable RSS feed generation, instead of mentioning generate_rss in DISABLED_PLUGINS.')
            self.config['GENERATE_RSS'] = False
            self.config['DISABLE_MAIN_RSS_FEED'] = True

        # PRETTY_URLS defaults to enabling STRIP_INDEXES unless explicitly disabled
        if self.config.get('PRETTY_URLS') and 'STRIP_INDEXES' not in config:
            self.config['STRIP_INDEXES'] = True

        if not self.config.get('COPY_SOURCES'):
            self.config['SHOW_SOURCELINK'] = False

        if self.config['CATEGORY_PATH']._inp is None:
            self.config['CATEGORY_PATH'] = self.config['TAG_PATH']
        if self.config['CATEGORY_PAGES_ARE_INDEXES'] is None:
            self.config['CATEGORY_PAGES_ARE_INDEXES'] = self.config['TAG_PAGES_ARE_INDEXES']

        self.default_lang = self.config['DEFAULT_LANG']
        self.translations = self.config['TRANSLATIONS']

        utils.LocaleBorg.initialize(self.config.get('LOCALES', {}), self.default_lang)

        # BASE_URL defaults to SITE_URL
        if 'BASE_URL' not in self.config:
            self.config['BASE_URL'] = self.config.get('SITE_URL')
        # BASE_URL should *always* end in /
        if self.config['BASE_URL'] and self.config['BASE_URL'][-1] != '/':
            utils.LOGGER.warning("Your BASE_URL doesn't end in / -- adding it, but please fix it in your config file!")
            self.config['BASE_URL'] += '/'

        try:
            _bnl = urlsplit(self.config['BASE_URL']).netloc
            _bnl.encode('ascii')
            urlsplit(self.config['SITE_URL']).netloc.encode('ascii')
        except (UnicodeEncodeError, UnicodeDecodeError):
            utils.LOGGER.error("Your BASE_URL or SITE_URL contains an IDN expressed in Unicode.  Please convert it to Punycode.")
            utils.LOGGER.error("Punycode of {}: {}".format(_bnl, _bnl.encode('idna')))
            sys.exit(1)

        # Load built-in metadata extractors
        metadata_extractors.load_defaults(self, self.metadata_extractors_by)
        if metadata_extractors.DEFAULT_EXTRACTOR is None:
            utils.LOGGER.error("Could not find default meta extractor ({})".format(
                metadata_extractors.DEFAULT_EXTRACTOR_NAME))
            sys.exit(1)

        # The Pelican metadata format requires a markdown extension
        if config.get('METADATA_FORMAT', 'nikola').lower() == 'pelican':
            if 'markdown.extensions.meta' not in config.get('MARKDOWN_EXTENSIONS', []) \
                    and 'markdown' in self.config['COMPILERS']:
                utils.LOGGER.warning(
                    'To use the Pelican metadata format, you need to add '
                    '"markdown.extensions.meta" to your MARKDOWN_EXTENSIONS setting.')

        # We use one global tzinfo object all over Nikola.
        try:
            self.tzinfo = dateutil.tz.gettz(self.config['TIMEZONE'])
        except Exception as exc:
            utils.LOGGER.warning("Error getting TZ: {}", exc)
            self.tzinfo = dateutil.tz.gettz()
        self.config['__tzinfo__'] = self.tzinfo

        # Store raw compilers for internal use (need a copy for that)
        self.config['_COMPILERS_RAW'] = {}
        for k, v in self.config['COMPILERS'].items():
            self.config['_COMPILERS_RAW'][k] = list(v)

        # Get search path for themes
        self.themes_dirs = ['themes'] + self.config['EXTRA_THEMES_DIRS']

        # Register default filters
        filter_name_format = 'filters.{0}'
        for filter_name, filter_definition in filters.__dict__.items():
            # Ignore objects whose name starts with an underscore, or which are not callable
            if filter_name.startswith('_') or not callable(filter_definition):
                continue
            # Register all other objects as filters
            self.register_filter(filter_name_format.format(filter_name), filter_definition)

        self._set_global_context_from_config()
        self._set_all_page_deps_from_config()
        # Read data files only if a site exists (Issue #2708)
        if self.configured:
            self._set_global_context_from_data()

        # Set persistent state facility
        self.state = Persistor('state_data.json')

        # Set cache facility
        self.cache = Persistor(os.path.join(self.config['CACHE_FOLDER'], 'cache_data.json'))

        # Create directories for persistors only if a site exists (Issue #2334)
        if self.configured:
            self.state._set_site(self)
            self.cache._set_site(self)

        # WebP files have no official MIME type yet, but we need to recognize them (Issue #3671)
        mimetypes.add_type('image/webp', '.webp')

    def _filter_duplicate_plugins(self, plugin_list: typing.Iterable[PluginCandidate]):
        """Find repeated plugins and discard the less local copy."""
        def plugin_position_in_places(plugin: PluginInfo):
            # plugin here is a tuple:
            # (path to the .plugin file, path to plugin module w/o .py, plugin metadata)
            for i, place in enumerate(self._plugin_places):
                place: pathlib.Path
                try:
                    # Path.is_relative_to backport
                    plugin.source_dir.relative_to(place)
                    return i
                except ValueError:
                    pass
            utils.LOGGER.warning("Duplicate plugin found in unexpected location: {}".format(plugin.source_dir))
            return len(self._plugin_places)

        plugin_dict = defaultdict(list)
        for plugin in plugin_list:
            plugin_dict[plugin.name].append(plugin)
        result = []
        for name, plugins in plugin_dict.items():
            if len(plugins) > 1:
                # Sort by locality
                plugins.sort(key=plugin_position_in_places)
                utils.LOGGER.debug("Plugin {} exists in multiple places, using {}".format(
                    name, plugins[-1].source_dir))
            result.append(plugins[-1])
        return result

    def init_plugins(self, commands_only=False, load_all=False):
        """Load plugins as needed."""
        extra_plugins_dirs = self.config['EXTRA_PLUGINS_DIRS']
        self._loading_commands_only = commands_only
        self._plugin_places = [
            resource_filename('nikola', 'plugins'),
            os.path.expanduser(os.path.join('~', '.nikola', 'plugins')),
            os.path.join(os.getcwd(), 'plugins'),
        ] + [path for path in extra_plugins_dirs if path]
        self._plugin_places = [pathlib.Path(p) for p in self._plugin_places]

        self.plugin_manager = PluginManager(plugin_places=self._plugin_places)

        compilers = defaultdict(set)
        # Also add aliases for combinations with TRANSLATIONS_PATTERN
        for compiler, exts in self.config['COMPILERS'].items():
            for ext in exts:
                compilers[compiler].add(ext)
                for lang in self.config['TRANSLATIONS'].keys():
                    candidate = utils.get_translation_candidate(self.config, "f" + ext, lang)
                    compilers[compiler].add(candidate)

        # Avoid redundant compilers (if load_all is False):
        # Remove compilers (and corresponding compiler extensions) that are not marked as
        # needed by any PostScanner plugin and put them into self.disabled_compilers
        # (respectively self.disabled_compiler_extensions).
        self.config['COMPILERS'] = {}
        self.disabled_compilers = {}
        self.disabled_compiler_extensions = defaultdict(list)

        candidates = self.plugin_manager.locate_plugins()
        good_candidates = set()
        if not load_all:
            for p in candidates:
                if commands_only:
                    if p.category != 'Command':
                        continue
                elif self.configured:  # Not commands-only, and configured
                    # Remove blacklisted plugins
                    if p.name in self.config['DISABLED_PLUGINS']:
                        utils.LOGGER.debug('Not loading disabled plugin {}', p.name)
                        continue
                    # Remove compilers - will be loaded later based on usage
                    if p.category == "PageCompiler":
                        self.disabled_compilers[p.name] = p
                        continue
                    # Remove compiler extensions we don't need
                    if p.compiler and p.compiler in self.disabled_compilers:
                        self.disabled_compiler_extensions[p.compiler].append(p)
                        continue
                good_candidates.add(p)

        good_candidates = self._filter_duplicate_plugins(good_candidates)
        self.plugin_manager.load_plugins(good_candidates)

        # Search for compiler plugins which we disabled but shouldn't have
        self._activate_plugins_of_category("PostScanner")
        if not load_all:
            file_extensions = set()
            for post_scanner in [p.plugin_object for p in self.plugin_manager.get_plugins_of_category('PostScanner')]:
                post_scanner: PostScanner
                exts = post_scanner.supported_extensions()
                if exts is not None:
                    file_extensions.update(exts)
                else:
                    # Stop scanning for more: once we get None, we have to load all compilers anyway
                    utils.LOGGER.debug("Post scanner {0!r} does not implement `supported_extensions`, loading all compilers".format(post_scanner))
                    file_extensions = None
                    break
            to_add = []
            for k, v in compilers.items():
                if file_extensions is None or file_extensions.intersection(v):
                    self.config['COMPILERS'][k] = sorted(list(v))
                    p = self.disabled_compilers.pop(k, None)
                    if p:
                        to_add.append(p)
                    for p in self.disabled_compiler_extensions.pop(k, []):
                        to_add.append(p)
            for _, p in self.disabled_compilers.items():
                utils.LOGGER.debug('Not loading unneeded compiler %s', p.name)
            for _, plugins in self.disabled_compiler_extensions.items():
                for p in plugins:
                    utils.LOGGER.debug('Not loading compiler extension %s', p.name)
            if to_add:
                extra_candidates = self._filter_duplicate_plugins(to_add)
                self.plugin_manager.load_plugins(extra_candidates)

        # Jupyter theme configuration.  If a website has ipynb enabled in post_pages
        # we should enable the Jupyter CSS (leaving that up to the theme itself).
        if 'needs_ipython_css' not in self._GLOBAL_CONTEXT:
            self._GLOBAL_CONTEXT['needs_ipython_css'] = 'ipynb' in self.config['COMPILERS']

        # Activate metadata extractors and prepare them for use
        for p in self._activate_plugins_of_category("MetadataExtractor"):
            metadata_extractors.classify_extractor(p.plugin_object, self.metadata_extractors_by)

        self._activate_plugins_of_category("Taxonomy")
        self.taxonomy_plugins = {}
        for taxonomy in [p.plugin_object for p in self.plugin_manager.get_plugins_of_category('Taxonomy')]:
            taxonomy: Taxonomy
            if not taxonomy.is_enabled():
                continue
            if taxonomy.classification_name in self.taxonomy_plugins:
                utils.LOGGER.error("Found more than one taxonomy with classification name '{}'!".format(taxonomy.classification_name))
                sys.exit(1)
            self.taxonomy_plugins[taxonomy.classification_name] = taxonomy

        self._activate_plugins_of_category("SignalHandler")

        # Emit signal for SignalHandlers which need to start running immediately.
        signal('sighandlers_loaded').send(self)

        self._commands = {}

        command_plugins = self._activate_plugins_of_category("Command")
        for plugin_info in command_plugins:
            plugin_info.plugin_object.short_help = plugin_info.description
            self._commands[plugin_info.name] = plugin_info.plugin_object

        self._activate_plugins_of_category("Task")
        self._activate_plugins_of_category("LateTask")
        self._activate_plugins_of_category("TaskMultiplier")

        # Activate all required compiler plugins
        self.compiler_extensions = self._activate_plugins_of_category("CompilerExtension")
        for plugin_info in self.plugin_manager.get_plugins_of_category("PageCompiler"):
            if plugin_info.name in self.config["COMPILERS"].keys():
                self._activate_plugin(plugin_info)

        # Activate shortcode plugins
        self._activate_plugins_of_category("ShortcodePlugin")

        # Load compiler plugins
        self.compilers = {}
        self.inverse_compilers = {}

        for plugin_info in self.plugin_manager.get_plugins_of_category("PageCompiler"):
            self.compilers[plugin_info.name] = plugin_info.plugin_object

        # Load comment systems, config plugins and register templated shortcodes
        self._activate_plugins_of_category("CommentSystem")
        self._activate_plugins_of_category("ConfigPlugin")
        self._register_templated_shortcodes()

        # Check with registered filters and configure filters
        for actions in self.config['FILTERS'].values():
            for i, f in enumerate(actions):
                if isinstance(f, str):
                    # Check whether this denotes a registered filter
                    _f = self.filters.get(f)
                    if _f is not None:
                        f = _f
                        actions[i] = f
                if hasattr(f, 'configuration_variables'):
                    args = {}
                    for arg, config in f.configuration_variables.items():
                        if config in self.config:
                            args[arg] = self.config[config]
                    if args:
                        actions[i] = functools.partial(f, **args)

        # Signal that we are configured
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
        self._GLOBAL_CONTEXT['index_display_post_count'] = self.config[
            'INDEX_DISPLAY_POST_COUNT']
        self._GLOBAL_CONTEXT['index_file'] = self.config['INDEX_FILE']
        self._GLOBAL_CONTEXT['use_bundles'] = self.config['USE_BUNDLES']
        self._GLOBAL_CONTEXT['use_cdn'] = self.config.get("USE_CDN")
        self._GLOBAL_CONTEXT['theme_color'] = self.config.get("THEME_COLOR")
        self._GLOBAL_CONTEXT['theme_config'] = self.config.get("THEME_CONFIG")
        self._GLOBAL_CONTEXT['favicons'] = self.config['FAVICONS']
        self._GLOBAL_CONTEXT['date_format'] = self.config.get('DATE_FORMAT')
        self._GLOBAL_CONTEXT['blog_author'] = self.config.get('BLOG_AUTHOR')
        self._GLOBAL_CONTEXT['blog_title'] = self.config.get('BLOG_TITLE')
        self._GLOBAL_CONTEXT['blog_email'] = self.config.get('BLOG_EMAIL')
        self._GLOBAL_CONTEXT['show_blog_title'] = self.config.get('SHOW_BLOG_TITLE')
        self._GLOBAL_CONTEXT['logo_url'] = self.config.get('LOGO_URL')
        self._GLOBAL_CONTEXT['blog_description'] = self.config.get('BLOG_DESCRIPTION')
        self._GLOBAL_CONTEXT['front_index_header'] = self.config.get('FRONT_INDEX_HEADER')
        self._GLOBAL_CONTEXT['color_hsl_adjust_hex'] = utils.color_hsl_adjust_hex
        self._GLOBAL_CONTEXT['colorize_str_from_base_color'] = utils.colorize_str_from_base_color
        self._GLOBAL_CONTEXT['blog_url'] = self.config.get('SITE_URL')
        self._GLOBAL_CONTEXT['template_hooks'] = self.template_hooks
        self._GLOBAL_CONTEXT['body_end'] = self.config.get('BODY_END')
        self._GLOBAL_CONTEXT['social_buttons_code'] = self.config.get('SOCIAL_BUTTONS_CODE')
        self._GLOBAL_CONTEXT['translations'] = self.config.get('TRANSLATIONS')
        self._GLOBAL_CONTEXT['license'] = self.config.get('LICENSE')
        self._GLOBAL_CONTEXT['search_form'] = self.config.get('SEARCH_FORM')
        self._GLOBAL_CONTEXT['comment_system'] = self.config.get('COMMENT_SYSTEM') or 'dummy'
        self._GLOBAL_CONTEXT['comment_system_id'] = self.config.get('COMMENT_SYSTEM_ID')
        self._GLOBAL_CONTEXT['site_has_comments'] = bool(self.config.get('COMMENT_SYSTEM'))
        self._GLOBAL_CONTEXT['mathjax_config'] = self.config.get(
            'MATHJAX_CONFIG')
        self._GLOBAL_CONTEXT['use_katex'] = self.config.get('USE_KATEX')
        self._GLOBAL_CONTEXT['katex_auto_render'] = self.config.get('KATEX_AUTO_RENDER')
        self._GLOBAL_CONTEXT['content_footer'] = self.config.get(
            'CONTENT_FOOTER')
        self._GLOBAL_CONTEXT['generate_atom'] = self.config.get('GENERATE_ATOM')
        self._GLOBAL_CONTEXT['generate_rss'] = self.config.get('GENERATE_RSS')
        self._GLOBAL_CONTEXT['rss_link'] = self.config.get('RSS_LINK')

        self._GLOBAL_CONTEXT['navigation_links'] = self.config.get('NAVIGATION_LINKS')
        self._GLOBAL_CONTEXT['navigation_alt_links'] = self.config.get('NAVIGATION_ALT_LINKS')

        self._GLOBAL_CONTEXT['twitter_card'] = self.config.get(
            'TWITTER_CARD', {})
        self._GLOBAL_CONTEXT['hide_sourcelink'] = not self.config.get(
            'SHOW_SOURCELINK')
        self._GLOBAL_CONTEXT['show_sourcelink'] = self.config.get(
            'SHOW_SOURCELINK')
        self._GLOBAL_CONTEXT['extra_head_data'] = self.config.get('EXTRA_HEAD_DATA')
        self._GLOBAL_CONTEXT['date_fanciness'] = self.config.get('DATE_FANCINESS')
        self._GLOBAL_CONTEXT['luxon_locales'] = LEGAL_VALUES['LUXON_LOCALES']
        self._GLOBAL_CONTEXT['luxon_date_format'] = self.config.get('LUXON_DATE_FORMAT')
        # TODO: remove in v9
        self._GLOBAL_CONTEXT['js_date_format'] = self.config.get('MOMENTJS_DATE_FORMAT')
        self._GLOBAL_CONTEXT['momentjs_locales'] = LEGAL_VALUES['MOMENTJS_LOCALES']
        # Patch missing locales into momentjs defaulting to English (Issue #3216)
        for l in self._GLOBAL_CONTEXT['translations']:
            if l not in self._GLOBAL_CONTEXT['momentjs_locales']:
                self._GLOBAL_CONTEXT['momentjs_locales'][l] = ""
        self._GLOBAL_CONTEXT['hidden_tags'] = self.config.get('HIDDEN_TAGS')
        self._GLOBAL_CONTEXT['hidden_categories'] = self.config.get('HIDDEN_CATEGORIES')
        self._GLOBAL_CONTEXT['hidden_authors'] = self.config.get('HIDDEN_AUTHORS')
        self._GLOBAL_CONTEXT['url_replacer'] = self.url_replacer
        self._GLOBAL_CONTEXT['sort_posts'] = utils.sort_posts
        self._GLOBAL_CONTEXT['smartjoin'] = utils.smartjoin
        self._GLOBAL_CONTEXT['colorize_str'] = utils.colorize_str
        self._GLOBAL_CONTEXT['meta_generator_tag'] = self.config.get('META_GENERATOR_TAG')
        self._GLOBAL_CONTEXT['multiple_authors_per_post'] = self.config.get('MULTIPLE_AUTHORS_PER_POST')

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
        # Offer global_data as an alias for data (Issue #2488)
        self._GLOBAL_CONTEXT['global_data'] = self._GLOBAL_CONTEXT['data']

    def _set_all_page_deps_from_config(self):
        """Save dependencies for all pages from configuration.

        Changes of values in this dict will force a rebuild of all pages.
        Unlike global context, contents are NOT available to templates.
        """
        self.ALL_PAGE_DEPS['atom_extension'] = self.config.get('ATOM_EXTENSION')
        self.ALL_PAGE_DEPS['atom_path'] = self.config.get('ATOM_PATH')
        self.ALL_PAGE_DEPS['rss_extension'] = self.config.get('RSS_EXTENSION')
        self.ALL_PAGE_DEPS['rss_path'] = self.config.get('RSS_PATH')
        self.ALL_PAGE_DEPS['rss_filename_base'] = self.config.get('RSS_FILENAME_BASE')
        self.ALL_PAGE_DEPS['atom_filename_base'] = self.config.get('ATOM_FILENAME_BASE')
        self.ALL_PAGE_DEPS['slug_author_path'] = self.config.get('SLUG_AUTHOR_PATH')
        self.ALL_PAGE_DEPS['slug_tag_path'] = self.config.get('SLUG_TAG_PATH')
        self.ALL_PAGE_DEPS['locale'] = self.config.get('LOCALE')
        self.ALL_PAGE_DEPS['index_read_more_link'] = self.config.get('INDEX_READ_MORE_LINK')
        self.ALL_PAGE_DEPS['feed_read_more_link'] = self.config.get('FEED_READ_MORE_LINK')

    def _activate_plugin(self, plugin_info: PluginInfo) -> None:
        plugin_info.plugin_object.set_site(self)

        if plugin_info.category == "TemplateSystem" or self._loading_commands_only:
            return

        templates_directory_candidates = [
            plugin_info.source_dir / "templates" / self.template_system.name,
            plugin_info.source_dir / plugin_info.module_name / "templates" / self.template_system.name
        ]
        for candidate in templates_directory_candidates:
            if candidate.exists() and candidate.is_dir():
                self.template_system.inject_directory(str(candidate))

    def _activate_plugins_of_category(self, category) -> typing.List[PluginInfo]:
        """Activate all the plugins of a given category and return them."""
        # this code duplicated in tests/base.py
        plugins = []
        for plugin_info in self.plugin_manager.get_plugins_of_category(category):
            self._activate_plugin(plugin_info)
            plugins.append(plugin_info)
        return plugins

    def _get_themes(self):
        if self._THEMES is None:
            try:
                self._THEMES = utils.get_theme_chain(self.config['THEME'], self.themes_dirs)
            except Exception:
                if self.config['THEME'] != LEGAL_VALUES['DEFAULT_THEME']:
                    utils.LOGGER.warning('''Cannot load theme "{0}", using '{1}' instead.'''.format(
                        self.config['THEME'], LEGAL_VALUES['DEFAULT_THEME']))
                    self.config['THEME'] = LEGAL_VALUES['DEFAULT_THEME']
                    return self._get_themes()
                raise
            # Check consistency of USE_CDN and the current THEME (Issue #386)
            if self.config['USE_CDN'] and self.config['USE_CDN_WARNING']:
                bootstrap_path = utils.get_asset_path(os.path.join(
                    'assets', 'css', 'bootstrap.min.css'), self._THEMES)
                if bootstrap_path and bootstrap_path.split(os.sep)[-4] not in ['bootstrap', 'bootstrap3', 'bootstrap4']:
                    utils.LOGGER.warning('The USE_CDN option may be incompatible with your theme, because it uses a hosted version of bootstrap.')

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
            pi = self.plugin_manager.get_plugin_by_name(template_sys_name, "TemplateSystem")
            if pi is None:
                sys.stderr.write("Error loading {0} template system "
                                 "plugin\n".format(template_sys_name))
                sys.exit(1)
            self._template_system = typing.cast(TemplateSystem, pi.plugin_object)
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
            compiler = self.inverse_compilers[ext]
        except KeyError:
            # Find the correct compiler for this files extension
            lang_exts_tab = list(self.config['COMPILERS'].items())
            langs = [lang for lang, exts in lang_exts_tab if ext in exts or
                     len([ext_ for ext_ in exts if source_name.endswith(ext_)]) > 0]
            if len(langs) != 1:
                if len(set(langs)) > 1:
                    sys.exit("Your file extension->compiler definition is "
                             "ambiguous.\nPlease remove one of the file "
                             "extensions from 'COMPILERS' in conf.py\n(The "
                             "error is in one of {0})".format(', '.join(langs)))
                elif len(langs) > 1:
                    langs = langs[:1]
                else:
                    sys.exit("COMPILERS in conf.py does not tell me how to "
                             "handle '{0}' extensions.".format(ext))

            lang = langs[0]
            try:
                compiler = self.compilers[lang]
            except KeyError:
                sys.exit("Cannot find '{0}' compiler; "
                         "it might require an extra plugin -- "
                         "do you have it installed?".format(lang))
            self.inverse_compilers[ext] = compiler

        return compiler

    def render_template(self, template_name, output_name, context, url_type=None, is_fragment=False):
        """Render a template with the global context.

        If ``output_name`` is None, will return a string and all URL
        normalization will be ignored (including the link:// scheme).
        If ``output_name`` is a string, URLs will be normalized and
        the resultant HTML will be saved to the named file (path must
        start with OUTPUT_FOLDER).

        The argument ``url_type`` allows to override the ``URL_TYPE``
        configuration.

        If ``is_fragment`` is set to ``True``, a HTML fragment will
        be rendered and not a whole HTML document.
        """
        local_context = {}
        local_context["template_name"] = template_name
        local_context.update(self.GLOBAL_CONTEXT)
        local_context.update(context)
        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            local_context[k] = local_context[k](local_context['lang'])
        local_context['is_rtl'] = local_context['lang'] in LEGAL_VALUES['RTL_LANGUAGES']
        local_context['url_type'] = self.config['URL_TYPE'] if url_type is None else url_type
        local_context["translations_feedorder"] = sorted(
            local_context["translations"],
            key=lambda x: (int(x != local_context['lang']), x)
        )
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

        if not output_name.startswith(self.config["OUTPUT_FOLDER"]):
            raise ValueError("Output path for templates must start with OUTPUT_FOLDER")
        url_part = output_name[len(self.config["OUTPUT_FOLDER"]) + 1:]

        # Treat our site as if output/ is "/" and then make all URLs relative,
        # making the site "relocatable"
        src = os.sep + url_part
        src = os.path.normpath(src)
        # The os.sep is because normpath will change "/" to "\" on windows
        src = "/".join(src.split(os.sep))

        utils.makedirs(os.path.dirname(output_name))
        parser = lxml.html.HTMLParser(remove_blank_text=True)
        if is_fragment:
            doc = lxml.html.fragment_fromstring(data.strip(), parser)
        else:
            doc = lxml.html.document_fromstring(data.strip(), parser)
        self.rewrite_links(doc, src, context['lang'], url_type)
        if is_fragment:
            # doc.text contains text before the first HTML, or None if there was no text
            # The text after HTML elements is added by tostring() (because its implicit
            # argument with_tail has default value True).
            data = (doc.text or '').encode('utf-8') + b''.join([lxml.html.tostring(child, encoding='utf-8', method='html') for child in doc.iterchildren()])
        else:
            data = lxml.html.tostring(doc, encoding='utf8', method='html', pretty_print=True, doctype='<!DOCTYPE html>')
        with open(output_name, "wb+") as post_file:
            post_file.write(data)

    def rewrite_links(self, doc, src, lang, url_type=None):
        """Replace links in document to point to the right places."""
        # First let lxml replace most of them
        doc.rewrite_links(lambda dst: self.url_replacer(src, dst, lang, url_type), resolve_base_href=False)

        # lxml ignores srcset in img and source elements, so do that by hand
        objs = list(doc.xpath('(//img|//source)'))
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
        # Avoid mangling links within the page
        if dst.startswith('#'):
            return dst

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
                if dst_url.query:
                    # If query strings are used in magic link, they will be
                    # passed to the path handler as keyword arguments (strings)
                    link_kwargs = {unquote(k): unquote(v[-1]) for k, v in parse_qs(dst_url.query).items()}
                else:
                    link_kwargs = {}

                # unquote from issue #2934
                dst = self.link(dst_url.netloc, unquote(dst_url.path.lstrip('/')), lang, **link_kwargs)
                if dst_url.fragment:
                    dst += '#' + dst_url.fragment
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
                    if isinstance(nl, bytes):
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
                return utils.full_path_from_urlparse(urlparse(dst))
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
                dst = utils.full_path_from_urlparse(parsed)
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

        if not result:
            raise ValueError("Failed to parse link: {0}".format((src, dst, i, src_elems, dst_elems)))

        return result

    def _make_renderfunc(self, t_data, fname=None):
        """Return a function that can be registered as a template shortcode.

        The returned function has access to the passed template data and
        accepts any number of positional and keyword arguments. Positional
        arguments values are added as a tuple under the key ``_args`` to the
        keyword argument dict and then the latter provides the template
        context.

        Global context keys are made available as part of the context,
        respecting locale.

        As a special quirk, the "data" key from global_context is
        available only as "global_data" because of name clobbering.

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
                dependencies = [fname] + self.template_system.get_deps(fname, context)
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
        dependencies = self.template_system.get_string_deps(t_data, context)
        return output, dependencies

    def register_shortcode(self, name, f):
        """Register function f to handle shortcode "name"."""
        if name in self.shortcode_registry:
            utils.LOGGER.warning('Shortcode name conflict: {}', name)
            return
        self.shortcode_registry[name] = f

    def apply_shortcodes(self, data, filename=None, lang=None, extra_context=None):
        """Apply shortcodes from the registry on data."""
        if extra_context is None:
            extra_context = {}
        if lang is None:
            lang = utils.LocaleBorg().current_lang
        return shortcodes.apply_shortcodes(data, self.shortcode_registry, self, filename, lang=lang, extra_context=extra_context)

    def apply_shortcodes_uuid(self, data, _shortcodes, filename=None, lang=None, extra_context=None):
        """Apply shortcodes from the registry on data."""
        if lang is None:
            lang = utils.LocaleBorg().current_lang
        if extra_context is None:
            extra_context = {}
        deps = []
        for k, v in _shortcodes.items():
            replacement, _deps = shortcodes.apply_shortcodes(v, self.shortcode_registry, self, filename, lang=lang, extra_context=extra_context)
            data = data.replace(k, replacement)
            deps.extend(_deps)
        return data, deps

    def _get_rss_copyright(self, lang, rss_plain):
        if rss_plain:
            return (
                self.config['RSS_COPYRIGHT_PLAIN'](lang) or
                lxml.html.fromstring(self.config['RSS_COPYRIGHT'](lang)).text_content().strip())
        else:
            return self.config['RSS_COPYRIGHT'](lang)

    def generic_rss_feed(self, lang, title, link, description, timeline,
                         rss_teasers, rss_plain, feed_length=10, feed_url=None,
                         enclosure=_enclosure, rss_links_append_query=None, copyright_=None):
        """Generate an ExtendedRSS2 feed object for later use."""
        rss_obj = utils.ExtendedRSS2(
            title=title,
            link=utils.encodelink(link),
            description=description,
            lastBuildDate=datetime.datetime.utcnow(),
            generator='Nikola (getnikola.com)',
            language=lang
        )

        if copyright_ is None:
            copyright_ = self._get_rss_copyright(lang, rss_plain)
        # Use the configured or specified copyright string if present.
        if copyright_:
            rss_obj.copyright = copyright_

        if feed_url:
            absurl = '/' + feed_url[len(self.config['BASE_URL']):]
            rss_obj.xsl_stylesheet_href = self.url_replacer(absurl, "/assets/xml/rss.xsl")

        items = []

        feed_append_query = None
        if rss_links_append_query:
            if rss_links_append_query is True:
                raise ValueError("RSS_LINKS_APPEND_QUERY (or FEED_LINKS_APPEND_QUERY) cannot be True. Valid values are False or a formattable string.")
            feed_append_query = rss_links_append_query.format(
                feedRelUri='/' + feed_url[len(self.config['BASE_URL']):],
                feedFormat="rss")

        for post in timeline[:feed_length]:
            data = post.text(lang, teaser_only=rss_teasers, strip_html=rss_plain,
                             feed_read_more_link=True, feed_links_append_query=feed_append_query)
            if feed_url is not None and data:
                # Massage the post's HTML (unless plain)
                if not rss_plain:
                    if 'previewimage' in post.meta[lang] and post.meta[lang]['previewimage'] not in data:
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
                            raise
            args = {
                'title': post.title(lang) if post.should_show_title() else None,
                'link': post.permalink(lang, absolute=True, query=feed_append_query),
                'description': data,
                # PyRSS2Gen's pubDate is GMT time.
                'pubDate': (post.date if post.date.tzinfo is None else
                            post.date.astimezone(dateutil.tz.tzutc())),
                'categories': post._tags.get(lang, []),
                'creator': post.author(lang),
                'guid': post.guid(lang),
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
        return rss_obj

    def generic_rss_renderer(self, lang, title, link, description, timeline, output_path,
                             rss_teasers, rss_plain, feed_length=10, feed_url=None,
                             enclosure=_enclosure, rss_links_append_query=None, copyright_=None):
        """Take all necessary data, and render a RSS feed in output_path."""
        rss_obj = self.generic_rss_feed(lang, title, link, description, timeline,
                                        rss_teasers, rss_plain, feed_length=feed_length, feed_url=feed_url,
                                        enclosure=enclosure, rss_links_append_query=rss_links_append_query, copyright_=copyright_)
        utils.rss_writer(rss_obj, output_path)

    def path(self, kind, name, lang=None, is_link=False, **kwargs):
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

        The returned value is either a path relative to output, like "categories/whatever.html", or
        an absolute URL ("https://getnikola.com/"), if path handler returns a string.

        If is_link is True, the path is absolute and uses "/" as separator
        (ex: "/archive/index.html").
        If is_link is False, the path is relative to output and uses the
        platform's separator.
        (ex: "archive\index.html")
        If the registered path handler returns a string instead of path component list - it's
        considered to be an absolute URL and returned as is.

        """
        if lang is None:
            lang = utils.LocaleBorg().current_lang

        try:
            path = self.path_handlers[kind](name, lang, **kwargs)
        except KeyError:
            utils.LOGGER.warning("Unknown path request of kind: {0}".format(kind))
            return ""

        # If path handler returns a string we consider it to be an absolute URL not requiring any
        # further processing, i.e 'https://getnikola.com/'. See Issue #2876.
        if isinstance(path, str):
            return path

        if path is None:
            path = "#"
        else:
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
            # URLs should always use forward slash separators, even on Windows
            return str(pathlib.PurePosixPath(*path))

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
        """Return a link to a post with given slug, if not ambiguous.

        Example:

        link://slug/yellow-camaro => /posts/cars/awful/yellow-camaro/index.html
        """
        results = [p for p in self.timeline if p.meta('slug') == name]
        if not results:
            utils.LOGGER.warning("Cannot resolve path request for slug: {0}".format(name))
        else:
            if len(results) > 1:
                utils.LOGGER.warning('Ambiguous path request for slug: {0}'.format(name))
            return [_f for _f in results[0].permalink(lang).split('/')]

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

    def link(self, *args, **kwargs):
        """Create a link."""
        url = self.path(*args, is_link=True, **kwargs)
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

    def register_filter(self, filter_name, filter_definition):
        """Register a filter.

        filter_name should be a name not confusable with an actual
        executable. filter_definition should be a callable accepting
        one argument (the filename).
        """
        if filter_name in self.filters:
            utils.LOGGER.warning('''The filter "{0}" is defined more than once.'''.format(filter_name))
        self.filters[filter_name] = filter_definition

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
        for pluginInfo in self.plugin_manager.get_plugins_of_category(plugin_category):
            for task in flatten(pluginInfo.plugin_object.gen_tasks()):
                if 'basename' not in task:
                    raise ValueError("Task {0} does not have a basename".format(task))
                task = self.clean_task_paths(task)
                if 'task_dep' not in task:
                    task['task_dep'] = []
                task['task_dep'].extend(self.injected_deps[task['basename']])
                yield task
                for multi in self.plugin_manager.get_plugins_of_category("TaskMultiplier"):
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
                return hierarchy_utils.parse_escaped_hierarchical_category_name(category_name)
            except Exception as e:
                utils.LOGGER.error(str(e))
                sys.exit(1)
        else:
            return [category_name] if len(category_name) > 0 else []

    def category_path_to_category_name(self, category_path):
        """Translate a category path to a category name."""
        if self.config['CATEGORY_ALLOW_HIERARCHIES']:
            return hierarchy_utils.join_hierarchical_category_path(category_path)
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
                node = hierarchy_utils.TreeNode(name, parent)
                node.children = create_hierarchy(children, node)
                node.category_path = [pn.name for pn in node.get_path()]
                node.category_name = self.category_path_to_category_name(node.category_path)
                self.category_hierarchy_lookup[node.category_name] = node
                if node.category_name not in self.config.get('HIDDEN_CATEGORIES'):
                    result.append(node)
            return natsort.natsorted(result, key=lambda e: e.name, alg=natsort.ns.F | natsort.ns.IC)

        root_list = create_hierarchy(self.category_hierarchy)
        # Next, flatten the hierarchy
        self.category_hierarchy = hierarchy_utils.flatten_tree_structure(root_list)

    @staticmethod
    def sort_posts_chronologically(posts, lang=None):
        """Sort a list of posts chronologically.

        This function also takes priority, title and source path into account.
        """
        # Last tie breaker: sort by source path (A-Z)
        posts = sorted(posts, key=lambda p: p.source_path)
        # Next tie breaker: sort by title if language is given (A-Z)
        if lang is not None:
            posts = natsort.natsorted(posts, key=lambda p: p.title(lang), alg=natsort.ns.F | natsort.ns.IC)
        # Next tie breaker: sort by date (reverse chronological order)
        posts = sorted(posts, key=lambda p: p.date, reverse=True)
        # Finally, sort by priority meta value (descending)
        posts = sorted(posts, key=lambda p: int(p.meta('priority')) if p.meta('priority') else 0, reverse=True)
        # Return result
        return posts

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

        for p in sorted(self.plugin_manager.get_plugins_of_category('PostScanner'), key=operator.attrgetter('name')):
            try:
                timeline = p.plugin_object.scan()
            except Exception:
                utils.LOGGER.error('Error reading timeline')
                raise
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
                if src_file is not None:
                    self.post_per_input_file[src_file] = post
                # deduplicate tags_per_language
                self.tags_per_language[lang] = list(set(self.tags_per_language[lang]))

        # Sort everything.

        self.timeline = self.sort_posts_chronologically(self.timeline)
        self.posts = self.sort_posts_chronologically(self.posts)
        self.all_posts = self.sort_posts_chronologically(self.all_posts)
        self.pages = self.sort_posts_chronologically(self.pages)
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

    def generic_renderer(self, lang, output_name, template_name, filters, file_deps=None, uptodate_deps=None, context=None, context_deps_remove=None, post_deps_dict=None, url_type=None, is_fragment=False):
        """Create tasks for rendering pages and post lists and other related pages.

        lang is the current language.
        output_name is the destination file name.
        template_name is the template to be used.
        filters is the list of filters (usually site.config['FILTERS']) which will be used to post-process the result.
        file_deps (optional) is a list of additional file dependencies (next to template and its dependencies).
        uptodate_deps (optional) is a list of additional entries added to the task's uptodate list.
        context (optional) a dict used as a basis for the template context. The lang parameter will always be added.
        context_deps_remove (optional) is a list of keys to remove from the context after using it as an uptodate dependency. This should name all keys containing non-trivial Python objects; they can be replaced by adding JSON-style dicts in post_deps_dict.
        post_deps_dict (optional) is a dict merged into the copy of context which is used as an uptodate dependency.
        url_type (optional) allows to override the ``URL_TYPE`` configuration.
        is_fragment (optional) allows to write a HTML fragment instead of a HTML document.
        """
        utils.LocaleBorg().set_locale(lang)

        template_dep_context = context.copy()
        template_dep_context.update(self.GLOBAL_CONTEXT)
        file_deps = copy(file_deps) if file_deps else []
        file_deps += self.template_system.template_deps(template_name, template_dep_context)
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
        deps_dict['all_page_deps'] = self.ALL_PAGE_DEPS
        if post_deps_dict:
            deps_dict.update(post_deps_dict)

        for k, v in self.GLOBAL_CONTEXT['template_hooks'].items():
            deps_dict['||template_hooks|{0}||'.format(k)] = v.calculate_deps()

        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            deps_dict[k] = deps_dict['global'][k](lang)
        for k in self._ALL_PAGE_DEPS_TRANSLATABLE:
            deps_dict[k] = deps_dict['all_page_deps'][k](lang)

        deps_dict['navigation_links'] = deps_dict['global']['navigation_links'](lang)
        deps_dict['navigation_alt_links'] = deps_dict['global']['navigation_alt_links'](lang)

        task = {
            'name': os.path.normpath(output_name),
            'targets': [output_name],
            'file_dep': file_deps,
            'actions': [(self.render_template, [template_name, output_name,
                                                context, url_type, is_fragment])],
            'clean': True,
            'uptodate': [config_changed(deps_dict, 'nikola.nikola.Nikola.generic_renderer')] + ([] if uptodate_deps is None else uptodate_deps)
        }

        return utils.apply_filters(task, filters)

    def generic_page_renderer(self, lang, post, filters, context=None):
        """Render post fragments to final HTML pages."""
        extension = post.compiler.extension()
        output_name = os.path.join(self.config['OUTPUT_FOLDER'],
                                   post.destination_path(lang, extension))

        deps = post.deps(lang)
        uptodate_deps = post.deps_uptodate(lang)
        deps.extend(utils.get_asset_path(x, self.THEMES) for x in ('bundles', 'parent', 'engine'))
        _theme_ini = utils.get_asset_path(self.config['THEME'] + '.theme', self.THEMES)
        if _theme_ini:
            deps.append(_theme_ini)

        context = copy(context) if context else {}
        context['post'] = post
        context['title'] = post.title(lang)
        context['description'] = post.description(lang)
        context['permalink'] = post.permalink(lang)
        if 'crumbs' not in context:
            crumb_path = post.permalink(lang).lstrip('/')
            if crumb_path.endswith(self.config['INDEX_FILE']):
                crumb_path = crumb_path[:-len(self.config['INDEX_FILE'])]
            if crumb_path.endswith('/'):
                context['crumbs'] = utils.get_crumbs(crumb_path.rstrip('/'), is_file=False)
            else:
                context['crumbs'] = utils.get_crumbs(crumb_path, is_file=True)
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

        signal('render_post').send({
            'site': self,
            'post': post,
            'lang': lang,
            'context': context,
            'deps_dict': deps_dict,
        })

        yield self.generic_renderer(lang, output_name, post.template_name, filters,
                                    file_deps=deps,
                                    uptodate_deps=uptodate_deps,
                                    context=context,
                                    context_deps_remove=['post'],
                                    post_deps_dict=deps_dict,
                                    url_type=post.url_type)

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
        if 'has_other_languages' not in context:
            context['has_other_languages'] = False

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
        blog_title = self.config['BLOG_TITLE'](lang)
        context["posts"] = posts
        context["title"] = blog_title
        context["description"] = self.config['BLOG_DESCRIPTION'](lang)
        context["lang"] = lang
        context.update(extra_context)

        context["title"] = "{0} ({1})".format(blog_title, context["title"]) if blog_title != context["title"] else blog_title

        deps_context = copy(context)
        deps_context["posts"] = [(p.meta[lang]['title'], p.permalink(lang)) for p in
                                 posts]
        deps_context["global"] = self.GLOBAL_CONTEXT
        deps_context["all_page_deps"] = self.ALL_PAGE_DEPS

        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            deps_context[k] = deps_context['global'][k](lang)
        for k in self._ALL_PAGE_DEPS_TRANSLATABLE:
            deps_context[k] = deps_context['all_page_deps'][k](lang)

        feed_xsl_link = self.abs_link("/assets/xml/atom.xsl")
        feed_root = lxml.etree.Element("feed")
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
                if 'previewimage' in post.meta[lang] and post.meta[lang]['previewimage'] not in text:
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
                        raise
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
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            atom_file.write(data)

    def generic_index_renderer(self, lang, posts, indexes_title, template_name, context_source, kw, basename, page_link, page_path, additional_dependencies=None):
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

        Note: if context['featured'] is present, it must be a list of posts,
        whose dependencies will be taken added to task['uptodate'].
        """
        # Update kw
        kw = kw.copy()
        kw["tag_pages_are_indexes"] = self.config['TAG_PAGES_ARE_INDEXES']
        kw["index_display_post_count"] = self.config['INDEX_DISPLAY_POST_COUNT']
        kw["index_teasers"] = self.config['INDEX_TEASERS']
        kw["indexes_pages"] = self.config['INDEXES_PAGES'](lang)
        kw["indexes_pages_main"] = self.config['INDEXES_PAGES_MAIN']
        kw["indexes_static"] = self.config['INDEXES_STATIC']
        kw['indexes_pretty_page_url'] = self.config["INDEXES_PRETTY_PAGE_URL"]
        kw['show_index_page_navigation'] = self.config['SHOW_INDEX_PAGE_NAVIGATION']

        if additional_dependencies is None:
            additional_dependencies = []

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
            if not lists:
                lists.append([])
        num_pages = len(lists)
        displayed_page_numbers = [utils.get_displayed_page_number(i, num_pages, self) for i in range(num_pages)]
        page_links = [page_link(i, page_number, num_pages, False) for i, page_number in enumerate(displayed_page_numbers)]
        if kw['show_index_page_navigation']:
            # Since the list displayed_page_numbers is not necessarily
            # sorted -- in case INDEXES_STATIC is True, it is of the
            # form [num_pages, 1, 2, ..., num_pages - 1] -- we order it
            # via a map. This allows to not replicate the logic of
            # utils.get_displayed_page_number() here.
            if not kw["indexes_pages_main"] and not kw["indexes_static"]:
                temp_map = {page_number: link for page_number, link in zip(displayed_page_numbers, page_links)}
            else:
                temp_map = {page_number - 1: link for page_number, link in zip(displayed_page_numbers, page_links)}
            page_links_context = [temp_map[i] for i in range(num_pages)]
        for i, post_list in enumerate(lists):
            context = context_source.copy()
            if 'pagekind' not in context:
                context['pagekind'] = ['index']
            if 'has_other_languages' not in context:
                context['has_other_languages'] = False
            ipages_i = displayed_page_numbers[i]
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
                context["prevlink"] = page_links[prevlink]
                context["prevfeedlink"] = page_link(prevlink, displayed_page_numbers[prevlink],
                                                    num_pages, False, extension=".atom")
            if nextlink is not None:
                context["nextlink"] = page_links[nextlink]
                context["nextfeedlink"] = page_link(nextlink, displayed_page_numbers[nextlink],
                                                    num_pages, False, extension=".atom")
            context['show_index_page_navigation'] = kw['show_index_page_navigation']
            if kw['show_index_page_navigation']:
                context['page_links'] = page_links_context
                if not kw["indexes_pages_main"] and not kw["indexes_static"]:
                    context['current_page'] = ipages_i
                else:
                    context['current_page'] = ipages_i - 1
                context['prev_next_links_reversed'] = kw['indexes_static']
            context["permalink"] = page_links[i]
            context["is_frontmost_index"] = i == 0

            # Add dependencies to featured posts
            if 'featured' in context:
                for post in context['featured']:
                    additional_dependencies += post.deps_uptodate(lang)

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

        if kw["indexes_pages_main"] and kw['indexes_pretty_page_url'](lang):
            # create redirection
            output_name = os.path.join(kw['output_folder'], page_path(0, displayed_page_numbers[0], num_pages, True))
            link = page_links[0]
            yield utils.apply_filters({
                'basename': basename,
                'name': output_name,
                'targets': [output_name],
                'actions': [(utils.create_redirect, (output_name, link))],
                'clean': True,
                'uptodate': [utils.config_changed(kw, 'nikola.nikola.Nikola.generic_index_renderer')],
            }, kw["filters"])

    def generic_atom_renderer(self, lang, posts, context_source, kw, basename, classification, kind, additional_dependencies=None):
        """Create an Atom feed.

        lang: The language
        posts: A list of posts
        context_source: This will be copied and extended and used as every
                        page's context
        kw: An extended version will be used for uptodate dependencies
        basename: Basename for task
        classification: name of current classification (used to generate links)
        kind: classification kind (used to generate links)
        additional_dependencies: a list of dependencies which will be added
                                 to task['uptodate']
        """
        # Update kw
        kw = kw.copy()
        kw["feed_length"] = self.config['FEED_LENGTH']
        kw['generate_atom'] = self.config["GENERATE_ATOM"]
        kw['feed_links_append_query'] = self.config["FEED_LINKS_APPEND_QUERY"]
        kw['feed_teasers'] = self.config['FEED_TEASERS']
        kw['feed_plain'] = self.config['FEED_PLAIN']

        if additional_dependencies is None:
            additional_dependencies = []

        post_list = posts[:kw["feed_length"]]
        feedlink = self.link(kind + "_atom", classification, lang)
        feedpath = self.path(kind + "_atom", classification, lang)

        context = context_source.copy()
        if 'has_other_languages' not in context:
            context['has_other_languages'] = False

        output_name = os.path.join(kw['output_folder'], feedpath)
        context["feedlink"] = feedlink
        task = {
            "basename": basename,
            "name": output_name,
            "file_dep": sorted([_.base_path for _ in post_list]),
            "task_dep": ['render_posts'],
            "targets": [output_name],
            "actions": [(self.atom_feed_renderer,
                         (lang,
                          post_list,
                          output_name,
                          kw['filters'],
                          context,))],
            "clean": True,
            "uptodate": [utils.config_changed(kw, 'nikola.nikola.Nikola.atom_feed_renderer')] + additional_dependencies
        }
        yield utils.apply_filters(task, kw['filters'])

    def __repr__(self):
        """Representation of a Nikola site."""
        return '<Nikola Site: {0!r}>'.format(self.config['BLOG_TITLE'](self.config['DEFAULT_LANG']))
