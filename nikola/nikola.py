# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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

from __future__ import print_function, unicode_literals
import io
from collections import defaultdict
from copy import copy
from pkg_resources import resource_filename
import datetime
import glob
import locale
import os
import json
import sys
import mimetypes
try:
    from urlparse import urlparse, urlsplit, urljoin
except ImportError:
    from urllib.parse import urlparse, urlsplit, urljoin  # NOQA

from blinker import signal
try:
    import pyphen
except ImportError:
    pyphen = None
import dateutil.tz

import logging
from . import DEBUG

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

import PyRSS2Gen as rss

import lxml.html
from yapsy.PluginManager import PluginManager

# Default "Read more..." link
DEFAULT_INDEX_READ_MORE_LINK = '<p class="more"><a href="{link}">{read_more}…</a></p>'
DEFAULT_RSS_READ_MORE_LINK = '<p><a href="{link}">{read_more}…</a> ({min_remaining_read})</p>'

# Default pattern for translation files' names
DEFAULT_TRANSLATIONS_PATTERN = '{path}.{lang}.{ext}'

from .post import Post
from . import utils
from .plugin_categories import (
    Command,
    LateTask,
    PageCompiler,
    RestExtension,
    MarkdownExtension,
    Task,
    TaskMultiplier,
    TemplateSystem,
    SignalHandler,
    ConfigPlugin,
)


config_changed = utils.config_changed

__all__ = ['Nikola']

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
        'bg': 'Bulgarian',
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
        'hi': 'Hindi',
        'hr': 'Croatian',
        'id': 'Indonesian',
        'it': 'Italian',
        ('ja', '!jp'): 'Japanese',
        'ko': 'Korean',
        'nb': 'Norwegian Bokmål',
        'nl': 'Dutch',
        'pl': 'Polish',
        'pt_br': 'Portuguese (Brasil)',
        'ru': 'Russian',
        'sk': 'Slovak',
        'sl': 'Slovene',
        'sr': 'Serbian (Cyrillic)',
        'sv': 'Swedish',
        ('tr', '!tr_TR'): 'Turkish',
        'ur': 'Urdu',
        'zh_cn': 'Chinese (Simplified)',
    },
    '_TRANSLATIONS_WITH_COUNTRY_SPECIFIERS': {
        # This dict is used in `init` in case of locales that exist with a
        # country specifier.  If there is no other locale that has the same
        # language with a different country, ``nikola init`` (but nobody else!)
        # will accept it, warning the user about it.
        'pt': 'pt_br',
        'zh': 'zh_cn'
    },
    'RTL_LANGUAGES': ('ar', 'fa', 'ur'),
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
        hr='hr',
        id='id',
        it='it',
        ja='ja',
        ko='kr',  # kr is South Korea, ko is the Korean language
        nb='no',
        nl='nl',
        pt_br='pt-br',
        pl='pl',
        ru='ru',
        sk='sk',
        sl='si',  # country code is si, language code is sl, colorbox is wrong
        sr='sr',  # warning: this is serbian in Latin alphabet
        sv='sv',
        tr='tr',
        zh_cn='zh-CN'
    ),
    'MOMENTJS_LOCALES': defaultdict(
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
        hr='hr',
        id='id',
        it='it',
        ja='ja',
        ko='ko',
        nb='nb',
        nl='nl',
        pt_br='pt-br',
        pl='pl',
        ru='ru',
        sk='sk',
        sl='sl',
        sr='sr-cyrl',
        sv='sv',
        tr='tr',
        zh_cn='zh-cn'
    ),
}


def _enclosure(post, lang):
    '''Default implementation of enclosures'''
    enclosure = post.meta('enclosure', lang)
    if enclosure:
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
            'filename': self.filename_path,
        }

        self.strict = False
        self.global_data = {}
        self.posts = []
        self.posts_per_year = defaultdict(list)
        self.posts_per_month = defaultdict(list)
        self.posts_per_tag = defaultdict(list)
        self.posts_per_category = defaultdict(list)
        self.post_per_file = {}
        self.timeline = []
        self.pages = []
        self._scanned = False
        self._template_system = None
        self._THEMES = None
        self.debug = DEBUG
        self.loghandlers = []
        self.colorful = config.pop('__colorful__', False)
        self.invariant = config.pop('__invariant__', False)
        self.quiet = config.pop('__quiet__', False)
        self.configured = bool(config)

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
            'BLOG_AUTHOR': 'Default Author',
            'BLOG_TITLE': 'Default Title',
            'BLOG_DESCRIPTION': 'Default Description',
            'BODY_END': "",
            'CACHE_FOLDER': 'cache',
            'CATEGORY_PATH': None,  # None means: same as TAG_PATH
            'CATEGORY_PAGES_ARE_INDEXES': None,  # None means: same as TAG_PAGES_ARE_INDEXES
            'CATEGORY_PAGES_DESCRIPTIONS': {},
            'CATEGORY_PREFIX': 'cat_',
            'CODE_COLOR_SCHEME': 'default',
            'COMMENT_SYSTEM': 'disqus',
            'COMMENTS_IN_GALLERIES': False,
            'COMMENTS_IN_STORIES': False,
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
            'COMMENT_SYSTEM_ID': 'nikolademo',
            'EXTRA_HEAD_DATA': '',
            'FAVICONS': {},
            'FEED_LENGTH': 10,
            'FILE_METADATA_REGEXP': None,
            'ADDITIONAL_METADATA': {},
            'FILES_FOLDERS': {'files': ''},
            'FILTERS': {},
            'FORCE_ISO8601': False,
            'GALLERY_FOLDERS': {'galleries': 'galleries'},
            'GALLERY_SORT_BY_DATE': True,
            'GLOBAL_CONTEXT_FILLER': [],
            'GZIP_COMMAND': None,
            'GZIP_FILES': False,
            'GZIP_EXTENSIONS': ('.txt', '.htm', '.html', '.css', '.js', '.json', '.xml'),
            'HYPHENATE': False,
            'IMAGE_FOLDERS': {'images': ''},
            'INDEX_DISPLAY_POST_COUNT': 10,
            'INDEX_FILE': 'index.html',
            'INDEX_TEASERS': False,
            'INDEXES_TITLE': "",
            'INDEXES_PAGES': "",
            'INDEXES_PAGES_MAIN': False,
            'INDEX_PATH': '',
            'IPYNB_CONFIG': {},
            'LESS_COMPILER': 'lessc',
            'LESS_OPTIONS': [],
            'LICENSE': '',
            'LINK_CHECK_WHITELIST': [],
            'LISTINGS_FOLDERS': {'listings': 'listings'},
            'LOGO_URL': '',
            'NAVIGATION_LINKS': {},
            'MARKDOWN_EXTENSIONS': ['fenced_code', 'codehilite'],
            'MAX_IMAGE_SIZE': 1280,
            'MATHJAX_CONFIG': '',
            'OLD_THEME_SUPPORT': True,
            'OUTPUT_FOLDER': 'output',
            'POSTS': (("posts/*.txt", "posts", "post.tmpl"),),
            'PAGES': (("stories/*.txt", "stories", "story.tmpl"),),
            'PANDOC_OPTIONS': [],
            'PRETTY_URLS': False,
            'FUTURE_IS_NOW': False,
            'INDEX_READ_MORE_LINK': DEFAULT_INDEX_READ_MORE_LINK,
            'RSS_READ_MORE_LINK': DEFAULT_RSS_READ_MORE_LINK,
            'RSS_LINKS_APPEND_QUERY': False,
            'REDIRECTIONS': [],
            'ROBOTS_EXCLUSIONS': [],
            'GENERATE_RSS': True,
            'RSS_LINK': None,
            'RSS_PATH': '',
            'RSS_PLAIN': False,
            'RSS_TEASERS': True,
            'SASS_COMPILER': 'sass',
            'SASS_OPTIONS': [],
            'SEARCH_FORM': '',
            'SHOW_BLOG_TITLE': True,
            'SHOW_SOURCELINK': True,
            'SHOW_UNTRANSLATED_POSTS': True,
            'SLUG_TAG_PATH': True,
            'SOCIAL_BUTTONS_CODE': SOCIAL_BUTTONS_CODE,
            'SITE_URL': 'http://getnikola.com/',
            'STORY_INDEX': False,
            'STRIP_INDEXES': False,
            'SITEMAP_INCLUDE_FILELESS_DIRS': True,
            'TAG_PATH': 'categories',
            'TAG_PAGES_ARE_INDEXES': False,
            'TAG_PAGES_DESCRIPTIONS': {},
            'TAGLIST_MINIMUM_POSTS': 1,
            'TEMPLATE_FILTERS': {},
            'THEME': 'bootstrap',
            'THEME_REVEAL_CONFIG_SUBTHEME': 'sky',
            'THEME_REVEAL_CONFIG_TRANSITION': 'cube',
            'THUMBNAIL_SIZE': 180,
            'UNSLUGIFY_TITLES': False,  # WARNING: conf.py.in overrides this with True for backwards compatibility
            'URL_TYPE': 'rel_path',
            'USE_BUNDLES': True,
            'USE_CDN': False,
            'USE_CDN_WARNING': True,
            'USE_FILENAME_AS_TITLE': True,
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
                                      'INDEX_READ_MORE_LINK',
                                      'RSS_READ_MORE_LINK',)

        self._GLOBAL_CONTEXT_TRANSLATABLE = ('blog_author',
                                             'blog_title',
                                             'blog_desc',  # TODO: remove in v8
                                             'blog_description',
                                             'license',
                                             'content_footer',
                                             'social_buttons_code',
                                             'search_form',
                                             'body_end',
                                             'extra_head_data',)
        # WARNING: navigation_links SHOULD NOT be added to the list above.
        #          Themes ask for [lang] there and we should provide it.

        for i in self.TRANSLATABLE_SETTINGS:
            try:
                self.config[i] = utils.TranslatableSetting(i, self.config[i], self.config['TRANSLATIONS'])
            except KeyError:
                pass

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

        if self.config['CATEGORY_PATH'] is None:
            self.config['CATEGORY_PATH'] = self.config['TAG_PATH']
        if self.config['CATEGORY_PAGES_ARE_INDEXES'] is None:
            self.config['CATEGORY_PAGES_ARE_INDEXES'] = self.config['TAG_PAGES_ARE_INDEXES']

        self.default_lang = self.config['DEFAULT_LANG']
        self.translations = self.config['TRANSLATIONS']

        if self.configured:
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

        # todo: remove in v8
        if not isinstance(self.config['DEPLOY_COMMANDS'], dict):
            utils.LOGGER.warn("A single list as DEPLOY_COMMANDS is deprecated.  DEPLOY_COMMANDS should be a dict, with deploy preset names as keys and lists of commands as values.")
            utils.LOGGER.warn("The key `default` is used by `nikola deploy`:")
            self.config['DEPLOY_COMMANDS'] = {'default': self.config['DEPLOY_COMMANDS']}
            utils.LOGGER.warn("DEPLOY_COMMANDS = {0}".format(self.config['DEPLOY_COMMANDS']))
            utils.LOGGER.info("(The above can be used with `nikola deploy` or `nikola deploy default`.  Multiple presets are accepted.)")

        # We use one global tzinfo object all over Nikola.
        self.tzinfo = dateutil.tz.gettz(self.config['TIMEZONE'])
        self.config['__tzinfo__'] = self.tzinfo

        self.plugin_manager = PluginManager(categories_filter={
            "Command": Command,
            "Task": Task,
            "LateTask": LateTask,
            "TemplateSystem": TemplateSystem,
            "PageCompiler": PageCompiler,
            "TaskMultiplier": TaskMultiplier,
            "RestExtension": RestExtension,
            "MarkdownExtension": MarkdownExtension,
            "SignalHandler": SignalHandler,
            "ConfigPlugin": ConfigPlugin,
        })
        self.plugin_manager.setPluginInfoExtension('plugin')
        extra_plugins_dirs = self.config['EXTRA_PLUGINS_DIRS']
        if sys.version_info[0] == 3:
            places = [
                resource_filename('nikola', 'plugins'),
                os.path.join(os.getcwd(), 'plugins'),
                os.path.expanduser('~/.nikola/plugins'),
            ] + [path for path in extra_plugins_dirs if path]
        else:
            places = [
                resource_filename('nikola', utils.sys_encode('plugins')),
                os.path.join(os.getcwd(), utils.sys_encode('plugins')),
                os.path.expanduser('~/.nikola/plugins'),
            ] + [utils.sys_encode(path) for path in extra_plugins_dirs if path]

        self.plugin_manager.setPluginPlaces(places)
        self.plugin_manager.collectPlugins()

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

        compilers = defaultdict(set)
        # Also add aliases for combinations with TRANSLATIONS_PATTERN
        for compiler, exts in self.config['COMPILERS'].items():
            for ext in exts:
                compilers[compiler].add(ext)
                for lang in self.config['TRANSLATIONS'].keys():
                    candidate = utils.get_translation_candidate(self.config, "f" + ext, lang)
                    compilers[compiler].add(candidate)

        # Avoid redundant compilers
        for k, v in compilers.items():
            self.config['COMPILERS'][k] = sorted(list(v))

        # Activate all required compiler plugins
        for plugin_info in self.plugin_manager.getPluginsOfCategory("PageCompiler"):
            if plugin_info.name in self.config["COMPILERS"].keys():
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)

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
        self._GLOBAL_CONTEXT['SLUG_TAG_PATH'] = self.config['SLUG_TAG_PATH']
        self._GLOBAL_CONTEXT['annotations'] = self.config['ANNOTATIONS']
        self._GLOBAL_CONTEXT['index_display_post_count'] = self.config[
            'INDEX_DISPLAY_POST_COUNT']
        self._GLOBAL_CONTEXT['use_bundles'] = self.config['USE_BUNDLES']
        self._GLOBAL_CONTEXT['use_cdn'] = self.config.get("USE_CDN")
        self._GLOBAL_CONTEXT['favicons'] = self.config['FAVICONS']
        self._GLOBAL_CONTEXT['date_format'] = self.config.get('DATE_FORMAT')
        self._GLOBAL_CONTEXT['blog_author'] = self.config.get('BLOG_AUTHOR')
        self._GLOBAL_CONTEXT['blog_title'] = self.config.get('BLOG_TITLE')
        self._GLOBAL_CONTEXT['show_blog_title'] = self.config.get('SHOW_BLOG_TITLE')
        self._GLOBAL_CONTEXT['logo_url'] = self.config.get('LOGO_URL')
        self._GLOBAL_CONTEXT['blog_description'] = self.config.get('BLOG_DESCRIPTION')

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
        self._GLOBAL_CONTEXT['subtheme'] = self.config.get('THEME_REVEAL_CONFIG_SUBTHEME')
        self._GLOBAL_CONTEXT['transition'] = self.config.get('THEME_REVEAL_CONFIG_TRANSITION')
        self._GLOBAL_CONTEXT['content_footer'] = self.config.get(
            'CONTENT_FOOTER')
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
        self._GLOBAL_CONTEXT['js_date_format'] = json.dumps(self.config.get('JS_DATE_FORMAT'))
        self._GLOBAL_CONTEXT['colorbox_locales'] = LEGAL_VALUES['COLORBOX_LOCALES']
        self._GLOBAL_CONTEXT['momentjs_locales'] = LEGAL_VALUES['MOMENTJS_LOCALES']
        self._GLOBAL_CONTEXT['url_replacer'] = self.url_replacer

        self._GLOBAL_CONTEXT.update(self.config.get('GLOBAL_CONTEXT', {}))

        # Load compiler plugins
        self.compilers = {}
        self.inverse_compilers = {}

        for plugin_info in self.plugin_manager.getPluginsOfCategory(
                "PageCompiler"):
            self.compilers[plugin_info.name] = \
                plugin_info.plugin_object

        self._activate_plugins_of_category("ConfigPlugin")

        signal('configured').send(self)

    def _activate_plugins_of_category(self, category):
        """Activate all the plugins of a given category and return them."""
        plugins = []
        for plugin_info in self.plugin_manager.getPluginsOfCategory(category):
            if plugin_info.name in self.config.get('DISABLED_PLUGINS'):
                self.plugin_manager.removePluginFromCategory(plugin_info, category)
            else:
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)
                plugins.append(plugin_info)
        return plugins

    def _get_themes(self):
        if self._THEMES is None:
            try:
                self._THEMES = utils.get_theme_chain(self.config['THEME'])
            except Exception:
                utils.LOGGER.warn('''Cannot load theme "{0}", using 'bootstrap' instead.'''.format(self.config['THEME']))
                self.config['THEME'] = 'bootstrap'
                return self._get_themes()
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
            return utils.load_messages(self.THEMES,
                                       self.translations,
                                       self.default_lang)
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
        """Get the correct compiler for a post from `conf.COMPILERS`
        To make things easier for users, the mapping in conf.py is
        compiler->[extensions], although this is less convenient for us. The
        majority of this function is reversing that dictionary and error
        checking.
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
                    exit("Your file extension->compiler definition is"
                         "ambiguous.\nPlease remove one of the file extensions"
                         "from 'COMPILERS' in conf.py\n(The error is in"
                         "one of {0})".format(', '.join(langs)))
                elif len(langs) > 1:
                    langs = langs[:1]
                else:
                    exit("COMPILERS in conf.py does not tell me how to "
                         "handle '{0}' extensions.".format(ext))

            lang = langs[0]
            compile_html = self.compilers[lang]
            self.inverse_compilers[ext] = compile_html

        return compile_html

    def render_template(self, template_name, output_name, context):
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
        doc = lxml.html.document_fromstring(data)
        doc.rewrite_links(lambda dst: self.url_replacer(src, dst, context['lang']))
        data = b'<!DOCTYPE html>\n' + lxml.html.tostring(doc, encoding='utf8', method='html', pretty_print=True)
        with open(output_name, "wb+") as post_file:
            post_file.write(data)

    def url_replacer(self, src, dst, lang=None, url_type=None):
        """URL mangler.

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

        # Refuse to replace links that are full URLs.
        if dst_url.netloc:
            if dst_url.scheme == 'link':  # Magic link
                dst = self.link(dst_url.netloc, dst_url.path.lstrip('/'), lang)
            else:
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

        if not result:
            result = "."

        # Don't forget the query part of the link
        if parsed_dst.query:
            result += "?" + parsed_dst.query

        # Don't forget the fragment (anchor) part of the link
        if parsed_dst.fragment:
            result += "#" + parsed_dst.fragment

        assert result, (src, dst, i, src_elems, dst_elems)

        return result

    def generic_rss_renderer(self, lang, title, link, description, timeline, output_path,
                             rss_teasers, rss_plain, feed_length=10, feed_url=None,
                             enclosure=_enclosure, rss_links_append_query=None):

        """Takes all necessary data, and renders a RSS feed in output_path."""
        rss_obj = utils.ExtendedRSS2(
            title=title,
            link=link,
            description=description,
            lastBuildDate=datetime.datetime.now(),
            generator='http://getnikola.com/',
            language=lang
        )

        if feed_url:
            rss_obj.xsl_stylesheet_href = self.url_replacer(feed_url, "/assets/xml/rss.xsl")

        items = []

        for post in timeline[:feed_length]:
            data = post.text(lang, teaser_only=rss_teasers, strip_html=rss_plain,
                             rss_read_more_link=True, rss_links_append_query=rss_links_append_query)
            if feed_url is not None and data:
                # Massage the post's HTML (unless plain)
                if not rss_plain:
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
                'link': post.permalink(lang, absolute=True, query=rss_links_append_query),
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
        """Build the path to a certain kind of page.

        These are mostly defined by plugins by registering via
        the register_path_handler method, except for slug and
        post_path which are defined in this class' init method.

        Here's some of the others, for historical reasons:

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
        * slug (name is the slug of a post or story)
        * filename (name is the source filename of a post/story, in DEFAULT_LANG, relative to conf.py)

        The returned value is always a path relative to output, like
        "categories/whatever.html"

        If is_link is True, the path is absolute and uses "/" as separator
        (ex: "/archive/index.html").
        If is_link is False, the path is relative to output and uses the
        platform's separator.
        (ex: "archive\\index.html")
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
        """post_path path handler"""
        return [_f for _f in [self.config['TRANSLATIONS'][lang],
                              os.path.dirname(name),
                              self.config['INDEX_FILE']] if _f]

    def slug_path(self, name, lang):
        """slug path handler"""
        results = [p for p in self.timeline if p.meta('slug') == name]
        if not results:
            utils.LOGGER.warning("Cannot resolve path request for slug: {0}".format(name))
        else:
            if len(results) > 1:
                utils.LOGGER.warning('Ambiguous path request for slug: {0}'.format(name))
            return [_f for _f in results[0].permalink(lang).split('/') if _f]

    def filename_path(self, name, lang):
        """filename path handler"""
        results = [p for p in self.timeline if p.source_path == name]
        if not results:
            utils.LOGGER.warning("Cannot resolve path request for filename: {0}".format(name))
        else:
            if len(results) > 1:
                utils.LOGGER.error("Ambiguous path request for filename: {0}".format(name))
            return [_f for _f in results[0].permalink(lang).split('/') if _f]

    def register_path_handler(self, kind, f):
        if kind in self.path_handlers:
            utils.LOGGER.warning('Conflicting path handlers for kind: {0}'.format(kind))
        else:
            self.path_handlers[kind] = f

    def link(self, *args):
        return self.path(*args, is_link=True)

    def abs_link(self, dst, protocol_relative=False):
        # Normalize
        if dst:  # Mako templates and empty strings evaluate to False
            dst = urljoin(self.config['BASE_URL'], dst.lstrip('/'))
        else:
            dst = self.config['BASE_URL']
        url = urlparse(dst).geturl()
        if protocol_relative:
            url = url.split(":", 1)[1]
        return url

    def rel_link(self, src, dst):
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
            return dst
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
        return '/'.join(['..'] * (len(src_elems) - i - 1) + dst_elems[i:])

    def file_exists(self, path, not_empty=False):
        """Returns True if the file exists. If not_empty is True,
        it also has to be not empty."""
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

        def flatten(task):
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

    def scan_posts(self, really=False, ignore_quit=False):
        """Scan all the posts."""
        if self._scanned and not really:
            return

        try:
            self.commands = utils.Commands(self.doit)
        except AttributeError:
            self.commands = None
        self.global_data = {}
        self.posts = []
        self.posts_per_year = defaultdict(list)
        self.posts_per_month = defaultdict(list)
        self.posts_per_tag = defaultdict(list)
        self.posts_per_category = defaultdict(list)
        self.post_per_file = {}
        self.timeline = []
        self.pages = []

        seen = set([])
        if not self.quiet:
            print("Scanning posts", end='', file=sys.stderr)
        slugged_tags = set([])
        quit = False
        for wildcard, destination, template_name, use_in_feeds in \
                self.config['post_pages']:
            if not self.quiet:
                print(".", end='', file=sys.stderr)
            dirname = os.path.dirname(wildcard)
            for dirpath, _, _ in os.walk(dirname, followlinks=True):
                dest_dir = os.path.normpath(os.path.join(destination,
                                            os.path.relpath(dirpath, dirname)))  # output/destination/foo/
                # Get all the untranslated paths
                dir_glob = os.path.join(dirpath, os.path.basename(wildcard))  # posts/foo/*.rst
                untranslated = glob.glob(dir_glob)
                # And now get all the translated paths
                translated = set([])
                for lang in self.config['TRANSLATIONS'].keys():
                    if lang == self.config['DEFAULT_LANG']:
                        continue
                    lang_glob = utils.get_translation_candidate(self.config, dir_glob, lang)  # posts/foo/*.LANG.rst
                    translated = translated.union(set(glob.glob(lang_glob)))
                # untranslated globs like *.rst often match translated paths too, so remove them
                # and ensure x.rst is not in the translated set
                untranslated = set(untranslated) - translated

                # also remove from translated paths that are translations of
                # paths in untranslated_list, so x.es.rst is not in the untranslated set
                for p in untranslated:
                    translated = translated - set([utils.get_translation_candidate(self.config, p, l) for l in self.config['TRANSLATIONS'].keys()])

                full_list = list(translated) + list(untranslated)
                # We eliminate from the list the files inside any .ipynb folder
                full_list = [p for p in full_list
                             if not any([x.startswith('.')
                                         for x in p.split(os.sep)])]

                for base_path in full_list:
                    if base_path in seen:
                        continue
                    else:
                        seen.add(base_path)
                    post = Post(
                        base_path,
                        self.config,
                        dest_dir,
                        use_in_feeds,
                        self.MESSAGES,
                        template_name,
                        self.get_compiler(base_path)
                    )
                    self.timeline.append(post)
                    self.global_data[post.source_path] = post
                    if post.use_in_feeds:
                        self.posts.append(post)
                        self.posts_per_year[
                            str(post.date.year)].append(post)
                        self.posts_per_month[
                            '{0}/{1:02d}'.format(post.date.year, post.date.month)].append(post)
                        for tag in post.alltags:
                            _tag_slugified = utils.slugify(tag)
                            if _tag_slugified in slugged_tags:
                                if tag not in self.posts_per_tag:
                                    # Tags that differ only in case
                                    other_tag = [existing for existing in self.posts_per_tag.keys() if utils.slugify(existing) == _tag_slugified][0]
                                    utils.LOGGER.error('You have tags that are too similar: {0} and {1}'.format(tag, other_tag))
                                    utils.LOGGER.error('Tag {0} is used in: {1}'.format(tag, post.source_path))
                                    utils.LOGGER.error('Tag {0} is used in: {1}'.format(other_tag, ', '.join([p.source_path for p in self.posts_per_tag[other_tag]])))
                                    quit = True
                            else:
                                slugged_tags.add(utils.slugify(tag, force=True))
                            self.posts_per_tag[tag].append(post)
                        self.posts_per_category[post.meta('category')].append(post)
                    else:
                        self.pages.append(post)
                    for lang in self.config['TRANSLATIONS'].keys():
                        self.post_per_file[post.destination_path(lang=lang)] = post
                        self.post_per_file[post.destination_path(lang=lang, extension=post.source_ext())] = post

        # Sort everything.
        self.timeline.sort(key=lambda p: p.date)
        self.timeline.reverse()
        self.posts.sort(key=lambda p: p.date)
        self.posts.reverse()
        self.pages.sort(key=lambda p: p.date)
        self.pages.reverse()

        for i, p in enumerate(self.posts[1:]):
            p.next_post = self.posts[i]
        for i, p in enumerate(self.posts[:-1]):
            p.prev_post = self.posts[i + 1]
        self._scanned = True
        if not self.quiet:
            print("done!", file=sys.stderr)

        signal('scanned').send(self)

        if quit and not ignore_quit:
            sys.exit(1)

    def generic_page_renderer(self, lang, post, filters):
        """Render post fragments to final HTML pages."""
        context = {}
        deps = post.deps(lang) + \
            self.template_system.template_deps(post.template_name)
        deps.extend(utils.get_asset_path(x, self.THEMES) for x in ('bundles', 'parent', 'engine'))
        deps = list(filter(None, deps))
        context['post'] = post
        context['lang'] = lang
        context['title'] = post.title(lang)
        context['description'] = post.description(lang)
        context['permalink'] = post.permalink(lang)
        if post.use_in_feeds:
            context['enable_comments'] = True
        else:
            context['enable_comments'] = self.config['COMMENTS_IN_STORIES']
        extension = self.get_compiler(post.source_path).extension()
        output_name = os.path.join(self.config['OUTPUT_FOLDER'],
                                   post.destination_path(lang, extension))
        deps_dict = copy(context)
        deps_dict.pop('post')
        if post.prev_post:
            deps_dict['PREV_LINK'] = [post.prev_post.permalink(lang)]
        if post.next_post:
            deps_dict['NEXT_LINK'] = [post.next_post.permalink(lang)]
        deps_dict['OUTPUT_FOLDER'] = self.config['OUTPUT_FOLDER']
        deps_dict['TRANSLATIONS'] = self.config['TRANSLATIONS']
        deps_dict['global'] = self.GLOBAL_CONTEXT
        deps_dict['comments'] = context['enable_comments']

        for k, v in self.GLOBAL_CONTEXT['template_hooks'].items():
            deps_dict['||template_hooks|{0}||'.format(k)] = v._items

        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            deps_dict[k] = deps_dict['global'][k](lang)

        deps_dict['navigation_links'] = deps_dict['global']['navigation_links'](lang)

        if post:
            deps_dict['post_translations'] = post.translated_to

        task = {
            'name': os.path.normpath(output_name),
            'file_dep': deps,
            'targets': [output_name],
            'actions': [(self.render_template, [post.template_name,
                                                output_name, context])],
            'clean': True,
            'uptodate': [config_changed(deps_dict, 'nikola.nikola.Nikola.generic_post_renderer')] + post.deps_uptodate(lang),
        }

        yield utils.apply_filters(task, filters)

    def generic_post_list_renderer(self, lang, posts, output_name,
                                   template_name, filters, extra_context):
        """Renders pages with lists of posts."""

        deps = self.template_system.template_deps(template_name)
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
        context.update(extra_context)
        deps_context = copy(context)
        deps_context["posts"] = [(p.meta[lang]['title'], p.permalink(lang)) for p in
                                 posts]
        deps_context["global"] = self.GLOBAL_CONTEXT

        for k, v in self.GLOBAL_CONTEXT['template_hooks'].items():
            deps_context['||template_hooks|{0}||'.format(k)] = v._items

        for k in self._GLOBAL_CONTEXT_TRANSLATABLE:
            deps_context[k] = deps_context['global'][k](lang)

        deps_context['navigation_links'] = deps_context['global']['navigation_links'](lang)

        task = {
            'name': os.path.normpath(output_name),
            'targets': [output_name],
            'file_dep': deps,
            'actions': [(self.render_template, [template_name, output_name,
                                                context])],
            'clean': True,
            'uptodate': [config_changed(deps_context, 'nikola.nikola.Nikola.generic_post_list_renderer')] + uptodate_deps
        }

        return utils.apply_filters(task, filters)

    def __repr__(self):
        return '<Nikola Site: {0!r}>'.format(self.config['BLOG_TITLE']())


def sanitized_locales(locale_fallback, locale_default, locales, translations):
    """Sanitizes all locales availble into a nikola session

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
            locales[lang] = locale_n

    return locale_fallback, locale_default, locales


def is_valid_locale(locale_n):
    """True if locale_n is acceptable for locale.setlocale

    for py2x compat locale_n should be of type str
    """
    try:
        locale.setlocale(locale.LC_ALL, locale_n)
        return True
    except locale.Error:
        return False


def valid_locale_fallback(desired_locale=None):
    """returns a default fallback_locale, a string that locale.setlocale will accept

    If desired_locale is provided must be of type str for py2x compatibility
    """
    # Whenever fallbacks change, adjust test TestHarcodedFallbacksWork
    candidates_windows = [str('English'), str('C')]
    candidates_posix = [str('en_US.utf8'), str('C')]
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
    locale_n = str(_windows_locale_guesses.get(lang, None))
    if not is_valid_locale(locale_n):
        locale_n = None
    return locale_n


def guess_locale_from_lang_posix(lang):
    # compatibility v6.0.4
    if is_valid_locale(str(lang)):
        locale_n = str(lang)
    else:
        # this works in Travis when locale support set by Travis suggestion
        locale_n = str((locale.normalize(lang).split('.')[0]) + '.utf8')
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


_windows_locale_guesses = {
    # some languages may need that the appropiate Microsoft's Language Pack
    # be instaled; the 'str' bit will be added in the guess function
    "bg": "Bulgarian",
    "ca": "Catalan",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "eo": "Esperanto",
    "es": "Spanish",
    "fa": "Farsi",  # Persian
    "fr": "French",
    "hr": "Croatian",
    "it": "Italian",
    "jp": "Japanese",
    "nl": "Dutch",
    "pl": "Polish",
    "pt_br": "Portuguese_Brazil",
    "ru": "Russian",
    "sl_si": "Slovenian",
    "tr_tr": "Turkish",
    "zh_cn": "Chinese_China",  # Chinese (Simplified)
}


SOCIAL_BUTTONS_CODE = """
<!-- Social buttons -->
<div id="addthisbox" class="addthis_toolbox addthis_peekaboo_style addthis_default_style addthis_label_style addthis_32x32_style">
<a class="addthis_button_more">Share</a>
<ul><li><a class="addthis_button_facebook"></a>
<li><a class="addthis_button_google_plusone_share"></a>
<li><a class="addthis_button_linkedin"></a>
<li><a class="addthis_button_twitter"></a>
</ul>
</div>
<script src="//s7.addthis.com/js/300/addthis_widget.js#pubid=ra-4f7088a56bb93798"></script>
<!-- End of social buttons -->
"""
