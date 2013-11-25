# -*- coding: utf-8 -*-

# Copyright © 2012-2013 Roberto Alsina and others.

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
from collections import defaultdict
from copy import copy
import glob
import locale
import os
import sys
try:
    from urlparse import urlparse, urlsplit, urljoin
except ImportError:
    from urllib.parse import urlparse, urlsplit, urljoin  # NOQA

from blinker import signal
try:
    import pyphen
except ImportError:
    pyphen = None

import logging
if os.getenv('NIKOLA_DEBUG'):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

import lxml.html
from yapsy.PluginManager import PluginManager

from .post import Post
from . import utils
from .plugin_categories import (
    Command,
    LateTask,
    PageCompiler,
    RestExtension,
    Task,
    TaskMultiplier,
    TemplateSystem,
    SignalHandler,
)


config_changed = utils.config_changed

__all__ = ['Nikola']


class Nikola(object):

    """Class that handles site generation.

    Takes a site config as argument on creation.
    """
    EXTRA_PLUGINS = [
        'planetoid',
        'ipynb',
        'local_search',
        'render_mustache',
    ]

    def __init__(self, **config):
        """Setup proper environment for running tasks."""

        # Register our own path handlers
        self.path_handlers = {
            'slug': self.slug_path,
            'post_path': self.post_path,
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
        self.loghandlers = []
        if not config:
            self.configured = False
        else:
            self.configured = True

        # This is the default config
        self.config = {
            'ADD_THIS_BUTTONS': True,
            'ANNOTATIONS': False,
            'ARCHIVE_PATH': "",
            'ARCHIVE_FILENAME': "archive.html",
            'BLOG_TITLE': 'Default Title',
            'BLOG_DESCRIPTION': 'Default Description',
            'BODY_END': "",
            'CACHE_FOLDER': 'cache',
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
            'COPY_SOURCES': True,
            'CREATE_MONTHLY_ARCHIVE': False,
            'CREATE_SINGLE_ARCHIVE': False,
            'DATE_FORMAT': '%Y-%m-%d %H:%M',
            'DEFAULT_LANG': "en",
            'DEPLOY_COMMANDS': [],
            'DISABLED_PLUGINS': (),
            'COMMENT_SYSTEM_ID': 'nikolademo',
            'ENABLED_EXTRAS': (),
            'EXTRA_HEAD_DATA': '',
            'FAVICONS': {},
            'FEED_LENGTH': 10,
            'FILE_METADATA_REGEXP': None,
            'ADDITIONAL_METADATA': {},
            'FILES_FOLDERS': {'files': ''},
            'FILTERS': {},
            'GALLERY_PATH': 'galleries',
            'GALLERY_SORT_BY_DATE': True,
            'GZIP_COMMAND': None,
            'GZIP_FILES': False,
            'GZIP_EXTENSIONS': ('.txt', '.htm', '.html', '.css', '.js', '.json', '.xml'),
            'HIDE_SOURCELINK': False,
            'HIDE_UNTRANSLATED_POSTS': False,
            'HYPHENATE': False,
            'INDEX_DISPLAY_POST_COUNT': 10,
            'INDEX_FILE': 'index.html',
            'INDEX_TEASERS': False,
            'INDEXES_TITLE': "",
            'INDEXES_PAGES': "",
            'INDEX_PATH': '',
            'IPYNB_CONFIG': {},
            'LICENSE': '',
            'LINK_CHECK_WHITELIST': [],
            'LISTINGS_FOLDER': 'listings',
            'NAVIGATION_LINKS': None,
            'MARKDOWN_EXTENSIONS': ['fenced_code', 'codehilite'],
            'MAX_IMAGE_SIZE': 1280,
            'MATHJAX_CONFIG': '',
            'OLD_THEME_SUPPORT': True,
            'OUTPUT_FOLDER': 'output',
            'POSTS': (("posts/*.txt", "posts", "post.tmpl"),),
            'PAGES': (("stories/*.txt", "stories", "story.tmpl"),),
            'PRETTY_URLS': False,
            'FUTURE_IS_NOW': False,
            'READ_MORE_LINK': '<p class="more"><a href="{link}">{read_more}…</a></p>',
            'REDIRECTIONS': [],
            'RSS_LINK': None,
            'RSS_PATH': '',
            'RSS_TEASERS': True,
            'SEARCH_FORM': '',
            'SLUG_TAG_PATH': True,
            'SOCIAL_BUTTONS_CODE': SOCIAL_BUTTONS_CODE,
            'SITE_URL': 'http://getnikola.com/',
            'STORY_INDEX': False,
            'STRIP_INDEXES': False,
            'SITEMAP_INCLUDE_FILELESS_DIRS': True,
            'TAG_PATH': 'categories',
            'TAG_PAGES_ARE_INDEXES': False,
            'THEME': 'bootstrap',
            'THEME_REVEAL_CONFIG_SUBTHEME': 'sky',
            'THEME_REVEAL_CONFIG_TRANSITION': 'cube',
            'THUMBNAIL_SIZE': 180,
            'URL_TYPE': 'rel_path',
            'USE_BUNDLES': True,
            'USE_CDN': False,
            'USE_FILENAME_AS_TITLE': True,
            'TIMEZONE': 'UTC',
            'DEPLOY_DRAFTS': True,
            'DEPLOY_FUTURE': False,
            'SCHEDULE_ALL': False,
            'SCHEDULE_RULE': '',
            'SCHEDULE_FORCE_TODAY': False,
            'LOGGING_HANDLERS': {'stderr': {'loglevel': 'WARNING', 'bubble': True}},
            'DEMOTE_HEADERS': 1,
        }

        self.config.update(config)

        # Make sure we have pyphen installed if we are using it
        if self.config.get('HYPHENATE') and pyphen is None:
            utils.LOGGER.warn('To use the hyphenation, you have to install '
                              'the "pyphen" package.')
            utils.LOGGER.warn('Setting HYPHENATE to False.')
            self.config['HYPHENATE'] = False

        # Deprecating post_compilers
        # TODO: remove on v7
        if 'post_compilers' in config:
            utils.LOGGER.warn('The post_compilers option is deprecated, use COMPILERS instead.')
            if 'COMPILERS' in config:
                utils.LOGGER.warn('COMPILERS conflicts with post_compilers, ignoring post_compilers.')
            else:
                self.config['COMPILERS'] = config['post_compilers']

        # Deprecating post_pages
        # TODO: remove on v7
        if 'post_pages' in config:
            utils.LOGGER.warn('The post_pages option is deprecated, use POSTS and PAGES instead.')
            if 'POSTS' in config or 'PAGES' in config:
                utils.LOGGER.warn('POSTS and PAGES conflict with post_pages, ignoring post_pages.')
            else:
                self.config['POSTS'] = [item[:3] for item in config['post_pages'] if item[-1]]
                self.config['PAGES'] = [item[:3] for item in config['post_pages'] if not item[-1]]
        # FIXME: Internally, we still use post_pages because it's a pain to change it
        self.config['post_pages'] = []
        for i1, i2, i3 in self.config['POSTS']:
            self.config['post_pages'].append([i1, i2, i3, True])
        for i1, i2, i3 in self.config['PAGES']:
            self.config['post_pages'].append([i1, i2, i3, False])

        # Deprecating DISQUS_FORUM
        # TODO: remove on v7
        if 'DISQUS_FORUM' in config:
            utils.LOGGER.warn('The DISQUS_FORUM option is deprecated, use COMMENT_SYSTEM_ID instead.')
            if 'COMMENT_SYSTEM_ID' in config:
                utils.LOGGER.warn('DISQUS_FORUM conflicts with COMMENT_SYSTEM_ID, ignoring DISQUS_FORUM.')
            else:
                self.config['COMMENT_SYSTEM_ID'] = config['DISQUS_FORUM']

        # Deprecating the ANALYTICS option
        # TODO: remove on v7
        if 'ANALYTICS' in config:
            utils.LOGGER.warn('The ANALYTICS option is deprecated, use BODY_END instead.')
            if 'BODY_END' in config:
                utils.LOGGER.warn('ANALYTICS conflicts with BODY_END, ignoring ANALYTICS.')
            else:
                self.config['BODY_END'] = config['ANALYTICS']

        # Deprecating the SIDEBAR_LINKS option
        # TODO: remove on v7
        if 'SIDEBAR_LINKS' in config:
            utils.LOGGER.warn('The SIDEBAR_LINKS option is deprecated, use NAVIGATION_LINKS instead.')
            if 'NAVIGATION_LINKS' in config:
                utils.LOGGER.warn('The SIDEBAR_LINKS conflicts with NAVIGATION_LINKS, ignoring SIDEBAR_LINKS.')
            else:
                self.config['NAVIGATION_LINKS'] = config['SIDEBAR_LINKS']
        # Compatibility alias
        self.config['SIDEBAR_LINKS'] = self.config['NAVIGATION_LINKS']

        if self.config['NAVIGATION_LINKS'] in (None, {}):
            self.config['NAVIGATION_LINKS'] = {self.config['DEFAULT_LANG']: ()}

        # Deprecating the ADD_THIS_BUTTONS option
        # TODO: remove on v7
        if 'ADD_THIS_BUTTONS' in config:
            utils.LOGGER.warn('The ADD_THIS_BUTTONS option is deprecated, use SOCIAL_BUTTONS_CODE instead.')
            if not config['ADD_THIS_BUTTONS']:
                utils.LOGGER.warn('Setting SOCIAL_BUTTONS_CODE to empty because ADD_THIS_BUTTONS is False.')
                self.config['SOCIAL_BUTTONS_CODE'] = ''

        # STRIP_INDEX_HTML config has been replaces with STRIP_INDEXES
        # Port it if only the oldef form is there
        # TODO: remove on v7
        if 'STRIP_INDEX_HTML' in config and 'STRIP_INDEXES' not in config:
            utils.LOGGER.warn('You should configure STRIP_INDEXES instead of STRIP_INDEX_HTML')
            self.config['STRIP_INDEXES'] = config['STRIP_INDEX_HTML']

        # PRETTY_URLS defaults to enabling STRIP_INDEXES unless explicitly disabled
        if config.get('PRETTY_URLS', False) and 'STRIP_INDEXES' not in config:
            self.config['STRIP_INDEXES'] = True

        if config.get('COPY_SOURCES') and not self.config['HIDE_SOURCELINK']:
            self.config['HIDE_SOURCELINK'] = True

        self.config['TRANSLATIONS'] = self.config.get('TRANSLATIONS',
                                                      {self.config['DEFAULT_LANG']: ''})

        # SITE_URL is required, but if the deprecated BLOG_URL
        # is available, use it and warn
        # TODO: remove on v7
        if 'SITE_URL' not in self.config:
            if 'BLOG_URL' in self.config:
                utils.LOGGER.warn('You should configure SITE_URL instead of BLOG_URL')
                self.config['SITE_URL'] = self.config['BLOG_URL']

        self.default_lang = self.config['DEFAULT_LANG']
        self.translations = self.config['TRANSLATIONS']

        locale_fallback, locale_default, locales = sanitized_locales(
                                    self.config.get('LOCALE_FALLBACK', None),
                                    self.config.get('LOCALE_DEFAULT', None),
                                    self.config.get('LOCALES', {}),
                                    self.translations)  # NOQA
        utils.LocaleBorg.initialize(locales, self.default_lang)

        # BASE_URL defaults to SITE_URL
        if 'BASE_URL' not in self.config:
            self.config['BASE_URL'] = self.config.get('SITE_URL')
        # BASE_URL should *always* end in /
        if self.config['BASE_URL'] and self.config['BASE_URL'][-1] != '/':
            utils.LOGGER.warn("Your BASE_URL doesn't end in / -- adding it.")

        self.plugin_manager = PluginManager(categories_filter={
            "Command": Command,
            "Task": Task,
            "LateTask": LateTask,
            "TemplateSystem": TemplateSystem,
            "PageCompiler": PageCompiler,
            "TaskMultiplier": TaskMultiplier,
            "RestExtension": RestExtension,
            "SignalHandler": SignalHandler,
        })
        self.plugin_manager.setPluginInfoExtension('plugin')
        if sys.version_info[0] == 3:
            places = [
                os.path.join(os.path.dirname(__file__), 'plugins'),
                os.path.join(os.getcwd(), 'plugins'),
            ]
        else:
            places = [
                os.path.join(os.path.dirname(__file__), utils.sys_encode('plugins')),
                os.path.join(os.getcwd(), utils.sys_encode('plugins')),
            ]
        self.plugin_manager.setPluginPlaces(places)
        self.plugin_manager.collectPlugins()

        # Activate all required SignalHandler plugins
        for plugin_info in self.plugin_manager.getPluginsOfCategory("SignalHandler"):
            if plugin_info.name in self.config.get('DISABLED_PLUGINS'):
                self.plugin_manager.removePluginFromCategory(plugin_info, "SignalHandler")
            else:
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)

        # Emit signal for SignalHandlers which need to start running immediately.
        signal('sighandlers_loaded').send(self)

        self.commands = {}
        # Activate all command plugins
        for plugin_info in self.plugin_manager.getPluginsOfCategory("Command"):
            if (plugin_info.name in self.config['DISABLED_PLUGINS']
                or (plugin_info.name in self.EXTRA_PLUGINS and
                    plugin_info.name not in self.config['ENABLED_EXTRAS'])):
                self.plugin_manager.removePluginFromCategory(plugin_info, "Command")
                continue

            self.plugin_manager.activatePluginByName(plugin_info.name)
            plugin_info.plugin_object.set_site(self)
            plugin_info.plugin_object.short_help = plugin_info.description
            self.commands[plugin_info.name] = plugin_info.plugin_object

        # Activate all task plugins
        for task_type in ["Task", "LateTask"]:
            for plugin_info in self.plugin_manager.getPluginsOfCategory(task_type):
                if (plugin_info.name in self.config['DISABLED_PLUGINS']
                    or (plugin_info.name in self.EXTRA_PLUGINS and
                        plugin_info.name not in self.config['ENABLED_EXTRAS'])):
                    self.plugin_manager.removePluginFromCategory(plugin_info, task_type)
                    continue
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)

        # Activate all multiplier plugins
        for plugin_info in self.plugin_manager.getPluginsOfCategory("TaskMultiplier"):
            if (plugin_info.name in self.config['DISABLED_PLUGINS']
                or (plugin_info.name in self.EXTRA_PLUGINS and
                    plugin_info.name not in self.config['ENABLED_EXTRAS'])):
                self.plugin_manager.removePluginFromCategory(plugin_info, task_type)
                continue
            self.plugin_manager.activatePluginByName(plugin_info.name)
            plugin_info.plugin_object.set_site(self)

        # Activate all required compiler plugins
        for plugin_info in self.plugin_manager.getPluginsOfCategory("PageCompiler"):
            if plugin_info.name in self.config["COMPILERS"].keys():
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)

        # set global_context for template rendering
        self._GLOBAL_CONTEXT = {}

        self._GLOBAL_CONTEXT['_link'] = self.link
        self._GLOBAL_CONTEXT['set_locale'] = utils.LocaleBorg().set_locale
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
        self._GLOBAL_CONTEXT['date_format'] = self.config.get(
            'DATE_FORMAT', '%Y-%m-%d %H:%M')
        self._GLOBAL_CONTEXT['blog_author'] = self.config.get('BLOG_AUTHOR')
        self._GLOBAL_CONTEXT['blog_title'] = self.config.get('BLOG_TITLE')

        # TODO: remove fallback in v7
        self._GLOBAL_CONTEXT['blog_url'] = self.config.get('SITE_URL', self.config.get('BLOG_URL'))
        self._GLOBAL_CONTEXT['blog_desc'] = self.config.get('BLOG_DESCRIPTION')
        self._GLOBAL_CONTEXT['body_end'] = self.config.get('BODY_END')
        # TODO: remove in v7
        self._GLOBAL_CONTEXT['analytics'] = self.config.get('BODY_END')
        # TODO: remove in v7
        self._GLOBAL_CONTEXT['add_this_buttons'] = self.config.get('SOCIAL_BUTTONS_CODE')
        self._GLOBAL_CONTEXT['social_buttons_code'] = self.config.get('SOCIAL_BUTTONS_CODE')
        self._GLOBAL_CONTEXT['translations'] = self.config.get('TRANSLATIONS')
        self._GLOBAL_CONTEXT['license'] = self.config.get('LICENSE')
        self._GLOBAL_CONTEXT['search_form'] = self.config.get('SEARCH_FORM')
        self._GLOBAL_CONTEXT['comment_system'] = self.config.get('COMMENT_SYSTEM')
        self._GLOBAL_CONTEXT['comment_system_id'] = self.config.get('COMMENT_SYSTEM_ID')
        # TODO: remove in v7
        self._GLOBAL_CONTEXT['disqus_forum'] = self.config.get('COMMENT_SYSTEM_ID')
        self._GLOBAL_CONTEXT['mathjax_config'] = self.config.get(
            'MATHJAX_CONFIG')
        self._GLOBAL_CONTEXT['subtheme'] = self.config.get('THEME_REVEAL_CONFIG_SUBTHEME')
        self._GLOBAL_CONTEXT['transition'] = self.config.get('THEME_REVEAL_CONFIG_TRANSITION')
        self._GLOBAL_CONTEXT['content_footer'] = self.config.get(
            'CONTENT_FOOTER')
        self._GLOBAL_CONTEXT['rss_path'] = self.config.get('RSS_PATH')
        self._GLOBAL_CONTEXT['rss_link'] = self.config.get('RSS_LINK')

        self._GLOBAL_CONTEXT['navigation_links'] = utils.Functionary(list, self.config['DEFAULT_LANG'])
        for k, v in self.config.get('NAVIGATION_LINKS', {}).items():
            self._GLOBAL_CONTEXT['navigation_links'][k] = v
        # TODO: remove on v7
        # Compatibility alias
        self._GLOBAL_CONTEXT['sidebar_links'] = self._GLOBAL_CONTEXT['navigation_links']

        self._GLOBAL_CONTEXT['twitter_card'] = self.config.get(
            'TWITTER_CARD', {})
        self._GLOBAL_CONTEXT['hide_sourcelink'] = self.config.get(
            'HIDE_SOURCELINK')
        self._GLOBAL_CONTEXT['extra_head_data'] = self.config.get('EXTRA_HEAD_DATA')

        self._GLOBAL_CONTEXT.update(self.config.get('GLOBAL_CONTEXT', {}))

        # Load compiler plugins
        self.compilers = {}
        self.inverse_compilers = {}

        for plugin_info in self.plugin_manager.getPluginsOfCategory(
                "PageCompiler"):
            self.compilers[plugin_info.name] = \
                plugin_info.plugin_object
        signal('configured').send(self)

    def _get_themes(self):
        if self._THEMES is None:
            # Check for old theme names (Issue #650) TODO: remove in v7
            theme_replacements = {
                'site': 'bootstrap',
                'orphan': 'base',
                'default': 'oldfashioned',
            }
            if self.config['THEME'] in theme_replacements:
                utils.LOGGER.warn('You are using the old theme "{0}", using "{1}" instead.'.format(
                    self.config['THEME'], theme_replacements[self.config['THEME']]))
                self.config['THEME'] = theme_replacements[self.config['THEME']]
                if self.config['THEME'] == 'oldfashioned':
                    utils.LOGGER.warn('''You may need to install the "oldfashioned" theme '''
                                      '''from themes.nikola.ralsina.com.ar because it's not '''
                                      '''shipped by default anymore.''')
                utils.LOGGER.warn('Please change your THEME setting.')
            try:
                self._THEMES = utils.get_theme_chain(self.config['THEME'])
            except Exception:
                utils.LOGGER.warn('''Can't load theme "{0}", using 'bootstrap' instead.'''.format(self.config['THEME']))
                self.config['THEME'] = 'bootstrap'
                return self._get_themes()
            # Check consistency of USE_CDN and the current THEME (Issue #386)
            if self.config['USE_CDN']:
                bootstrap_path = utils.get_asset_path(os.path.join(
                    'assets', 'css', 'bootstrap.min.css'), self._THEMES)
                if bootstrap_path and bootstrap_path.split(os.sep)[-4] not in ['bootstrap', 'bootstrap3']:
                    utils.LOGGER.warn('The USE_CDN option may be incompatible with your theme, because it uses a hosted version of bootstrap.')

        return self._THEMES

    THEMES = property(_get_themes)

    def _get_messages(self):
        return utils.load_messages(self.THEMES,
                                   self.translations,
                                   self.default_lang)

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
            langs = [lang for lang, exts in
                     list(self.config['COMPILERS'].items())
                     if ext in exts]
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
        # string, arguments
        local_context["formatmsg"] = lambda s, *a: s % a
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

        parsed_src = urlsplit(src)
        src_elems = parsed_src.path.split('/')[1:]

        def replacer(dst):
            # Refuse to replace links that are full URLs.
            dst_url = urlparse(dst)
            if dst_url.netloc:
                if dst_url.scheme == 'link':  # Magic link
                    dst = self.link(dst_url.netloc, dst_url.path.lstrip('/'),
                                    context['lang'])
                else:
                    return dst

            # Normalize
            dst = urljoin(src, dst)

            # Avoid empty links.
            if src == dst:
                if self.config.get('URL_TYPE') == 'absolute':
                    dst = urljoin(self.config['BASE_URL'], dst)
                    return dst
                elif self.config.get('URL_TYPE') == 'full_path':
                    return dst
                else:
                    return "#"

            # Check that link can be made relative, otherwise return dest
            parsed_dst = urlsplit(dst)
            if parsed_src[:2] != parsed_dst[:2]:
                if self.config.get('URL_TYPE') == 'absolute':
                    dst = urljoin(self.config['BASE_URL'], dst)
                return dst

            if self.config.get('URL_TYPE') in ('full_path', 'absolute'):
                if self.config.get('URL_TYPE') == 'absolute':
                    dst = urljoin(self.config['BASE_URL'], dst)
                return dst

            # Now both paths are on the same site and absolute
            dst_elems = parsed_dst.path.split('/')[1:]

            i = 0
            for (i, s), d in zip(enumerate(src_elems), dst_elems):
                if s != d:
                    break
            # Now i is the longest common prefix
            result = '/'.join(['..'] * (len(src_elems) - i - 1) +
                              dst_elems[i:])

            if not result:
                result = "."

            # Don't forget the fragment (anchor) part of the link
            if parsed_dst.fragment:
                result += "#" + parsed_dst.fragment

            assert result, (src, dst, i, src_elems, dst_elems)

            return result

        utils.makedirs(os.path.dirname(output_name))
        doc = lxml.html.document_fromstring(data)
        doc.rewrite_links(replacer)
        data = b'<!DOCTYPE html>' + lxml.html.tostring(doc, encoding='utf8')
        with open(output_name, "wb+") as post_file:
            post_file.write(data)

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

        path = self.path_handlers[kind](name, lang)

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

    def post_path(self, name, lang):
        """post_path path handler"""
        return [_f for _f in [self.config['TRANSLATIONS'][lang],
                              os.path.dirname(name),
                              self.config['INDEX_FILE']] if _f]

    def slug_path(self, name, lang):
        """slug path handler"""
        results = [p for p in self.timeline if p.meta('slug') == name]
        if not results:
            utils.LOGGER.warning("Can't resolve path request for slug: {0}".format(name))
        else:
            if len(results) > 1:
                utils.LOGGER.warning('Ambiguous path request for slug: {0}'.format(name))
            return [_f for _f in results[0].permalink(lang).split('/') if _f]

    def register_path_handler(self, kind, f):
        if kind in self.path_handlers:
            utils.LOGGER.warning('Conflicting path handlers for kind: {0}'.format(kind))
        else:
            self.path_handlers[kind] = f

    def link(self, *args):
        return self.path(*args, is_link=True)

    def abs_link(self, dst):
        # Normalize
        dst = urljoin(self.config['BASE_URL'], dst)

        return urlparse(dst).path

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

    def scan_posts(self):
        """Scan all the posts."""
        if self._scanned:
            return
        seen = set([])
        print("Scanning posts", end='', file=sys.stderr)
        lower_case_tags = set([])
        for wildcard, destination, template_name, use_in_feeds in \
                self.config['post_pages']:
            print(".", end='', file=sys.stderr)
            dirname = os.path.dirname(wildcard)
            for dirpath, _, _ in os.walk(dirname):
                dir_glob = os.path.join(dirpath, os.path.basename(wildcard))
                dest_dir = os.path.normpath(os.path.join(destination,
                                            os.path.relpath(dirpath, dirname)))
                full_list = glob.glob(dir_glob)
                # Now let's look for things that are not in default_lang
                for lang in self.config['TRANSLATIONS'].keys():
                    lang_glob = dir_glob + "." + lang
                    translated_list = glob.glob(lang_glob)
                    for fname in translated_list:
                        orig_name = os.path.splitext(fname)[0]
                        if orig_name in full_list:
                            continue
                        full_list.append(orig_name)
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
                    self.global_data[post.source_path] = post
                    if post.use_in_feeds:
                        self.posts.append(post.source_path)
                        self.posts_per_year[
                            str(post.date.year)].append(post.source_path)
                        self.posts_per_month[
                            '{0}/{1:02d}'.format(post.date.year, post.date.month)].append(post.source_path)
                        for tag in post.alltags:
                            if tag.lower() in lower_case_tags:
                                if tag not in self.posts_per_tag:
                                    # Tags that differ only in case
                                    other_tag = [k for k in self.posts_per_tag.keys() if k.lower() == tag.lower()][0]
                                    utils.LOGGER.error('You have cases that differ only in upper/lower case: {0} and {1}'.format(tag, other_tag))
                                    utils.LOGGER.error('Tag {0} is used in: {1}'.format(tag, post.source_path))
                                    utils.LOGGER.error('Tag {0} is used in: {1}'.format(other_tag, ', '.join(self.posts_per_tag[other_tag])))
                                    sys.exit(1)
                            else:
                                lower_case_tags.add(tag.lower())
                            self.posts_per_tag[tag].append(post.source_path)
                        self.posts_per_category[post.meta('category')].append(post.source_path)
                    else:
                        self.pages.append(post)
                    self.post_per_file[post.destination_path(lang=lang)] = post
                    self.post_per_file[post.destination_path(lang=lang, extension=post.source_ext())] = post

        for name, post in list(self.global_data.items()):
            self.timeline.append(post)
        self.timeline.sort(key=lambda p: p.date)
        self.timeline.reverse()
        post_timeline = [p for p in self.timeline if p.use_in_feeds]
        for i, p in enumerate(post_timeline[1:]):
            p.next_post = post_timeline[i]
        for i, p in enumerate(post_timeline[:-1]):
            p.prev_post = post_timeline[i + 1]
        self._scanned = True
        print("done!", file=sys.stderr)

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
        context['page_list'] = self.pages
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
        if post:
            deps_dict['post_translations'] = post.translated_to

        task = {
            'name': os.path.normpath(output_name),
            'file_dep': deps,
            'targets': [output_name],
            'actions': [(self.render_template, [post.template_name,
                                                output_name, context])],
            'clean': True,
            'uptodate': [config_changed(deps_dict)],
        }

        yield utils.apply_filters(task, filters)

    def generic_post_list_renderer(self, lang, posts, output_name,
                                   template_name, filters, extra_context):
        """Renders pages with lists of posts."""

        deps = self.template_system.template_deps(template_name)
        for post in posts:
            deps += post.deps(lang)
        context = {}
        context["posts"] = posts
        context["title"] = self.config['BLOG_TITLE']
        context["description"] = self.config['BLOG_DESCRIPTION']
        context["lang"] = lang
        context["prevlink"] = None
        context["nextlink"] = None
        context.update(extra_context)
        deps_context = copy(context)
        deps_context["posts"] = [(p.meta[lang]['title'], p.permalink(lang)) for p in
                                 posts]
        deps_context["global"] = self.GLOBAL_CONTEXT
        task = {
            'name': os.path.normpath(output_name),
            'targets': [output_name],
            'file_dep': deps,
            'actions': [(self.render_template, [template_name, output_name,
                                                context])],
            'clean': True,
            'uptodate': [config_changed(deps_context)]
        }

        return utils.apply_filters(task, filters)


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
    "fa": "Farsi",  # persian
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
<script type="text/javascript" src="//s7.addthis.com/js/300/addthis_widget.js#pubid=ra-4f7088a56bb93798"></script>
<!-- End of social buttons -->
"""
