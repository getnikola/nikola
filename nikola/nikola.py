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
import warnings

import lxml.html
from yapsy.PluginManager import PluginManager
import pytz

if os.getenv('NIKOLA_DEBUG'):
    import logging
    logging.basicConfig(level=logging.DEBUG)
else:
    import logging
    logging.basicConfig(level=logging.ERROR)

from .post import Post
from . import utils
from .plugin_categories import (
    Command,
    LateTask,
    PageCompiler,
    Task,
    TaskMultiplier,
    TemplateSystem,
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

        self.global_data = {}
        self.posts_per_year = defaultdict(list)
        self.posts_per_month = defaultdict(list)
        self.posts_per_tag = defaultdict(list)
        self.post_per_file = {}
        self.timeline = []
        self.pages = []
        self._scanned = False
        if not config:
            self.configured = False
        else:
            self.configured = True

        # This is the default config
        self.config = {
            'ADD_THIS_BUTTONS': True,
            'ANALYTICS': '',
            'ARCHIVE_PATH': "",
            'ARCHIVE_FILENAME': "archive.html",
            'CACHE_FOLDER': 'cache',
            'CODE_COLOR_SCHEME': 'default',
            'COMMENTS_IN_GALLERIES': False,
            'COMMENTS_IN_STORIES': False,
            'CONTENT_FOOTER': '',
            'CREATE_MONTHLY_ARCHIVE': False,
            'DATE_FORMAT': '%Y-%m-%d %H:%M',
            'DEFAULT_LANG': "en",
            'DEPLOY_COMMANDS': [],
            'DISABLED_PLUGINS': (),
            'DISQUS_FORUM': 'nikolademo',
            'ENABLED_EXTRAS': (),
            'EXTRA_HEAD_DATA': '',
            'FAVICONS': {},
            'FILE_METADATA_REGEXP': None,
            'FILES_FOLDERS': {'files': ''},
            'FILTERS': {},
            'GALLERY_PATH': 'galleries',
            'GZIP_FILES': False,
            'GZIP_EXTENSIONS': ('.txt', '.htm', '.html', '.css', '.js', '.json'),
            'HIDE_UNTRANSLATED_POSTS': False,
            'INDEX_DISPLAY_POST_COUNT': 10,
            'INDEX_FILE': 'index.html',
            'INDEX_TEASERS': False,
            'INDEXES_TITLE': "",
            'INDEXES_PAGES': "",
            'INDEX_PATH': '',
            'LICENSE': '',
            'LINK_CHECK_WHITELIST': [],
            'LISTINGS_FOLDER': 'listings',
            'MARKDOWN_EXTENSIONS': ['fenced_code', 'codehilite'],
            'MAX_IMAGE_SIZE': 1280,
            'MATHJAX_CONFIG': '',
            'OLD_THEME_SUPPORT': True,
            'OUTPUT_FOLDER': 'output',
            'post_compilers': {
                "rest": ('.txt', '.rst'),
                "markdown": ('.md', '.mdown', '.markdown'),
                "textile": ('.textile',),
                "txt2tags": ('.t2t',),
                "bbcode": ('.bb',),
                "wiki": ('.wiki',),
                "ipynb": ('.ipynb',),
                "html": ('.html', '.htm')
            },
            'POST_PAGES': (
                ("posts/*.txt", "posts", "post.tmpl", True),
                ("stories/*.txt", "stories", "story.tmpl", False),
            ),
            'PRETTY_URLS': False,
            'REDIRECTIONS': [],
            'RSS_LINK': None,
            'RSS_PATH': '',
            'RSS_TEASERS': True,
            'SEARCH_FORM': '',
            'SLUG_TAG_PATH': True,
            'STORY_INDEX': False,
            'STRIP_INDEXES': False,
            'SITEMAP_INCLUDE_FILELESS_DIRS': True,
            'TAG_PATH': 'categories',
            'TAG_PAGES_ARE_INDEXES': False,
            'THEME': 'site',
            'THEME_REVEAL_CONGIF_SUBTHEME': 'sky',
            'THEME_REVEAL_CONGIF_TRANSITION': 'cube',
            'THUMBNAIL_SIZE': 180,
            'USE_BUNDLES': True,
            'USE_CDN': False,
            'USE_FILENAME_AS_TITLE': True,
            'TIMEZONE': None,
        }

        self.config.update(config)

        # STRIP_INDEX_HTML config has been replaces with STRIP_INDEXES
        # Port it if only the oldef form is there
        if 'STRIP_INDEX_HTML' in config and 'STRIP_INDEXES' not in config:
            print("WARNING: You should configure STRIP_INDEXES instead of STRIP_INDEX_HTML")
            self.config['STRIP_INDEXES'] = config['STRIP_INDEX_HTML']

        # PRETTY_URLS defaults to enabling STRIP_INDEXES unless explicitly disabled
        if config.get('PRETTY_URLS', False) and 'STRIP_INDEXES' not in config:
            self.config['STRIP_INDEXES'] = True

        self.config['TRANSLATIONS'] = self.config.get('TRANSLATIONS',
                                                      {self.config['DEFAULT_'
                                                      'LANG']: ''})

        self.THEMES = utils.get_theme_chain(self.config['THEME'])

        self.MESSAGES = utils.load_messages(self.THEMES,
                                            self.config['TRANSLATIONS'],
                                            self.config['DEFAULT_LANG'])

        # SITE_URL is required, but if the deprecated BLOG_URL
        # is available, use it and warn
        if 'SITE_URL' not in self.config:
            if 'BLOG_URL' in self.config:
                print("WARNING: You should configure SITE_URL instead of BLOG_URL")
                self.config['SITE_URL'] = self.config['BLOG_URL']

        self.default_lang = self.config['DEFAULT_LANG']
        self.translations = self.config['TRANSLATIONS']

        # BASE_URL defaults to SITE_URL
        if 'BASE_URL' not in self.config:
            self.config['BASE_URL'] = self.config.get('SITE_URL')

        self.plugin_manager = PluginManager(categories_filter={
            "Command": Command,
            "Task": Task,
            "LateTask": LateTask,
            "TemplateSystem": TemplateSystem,
            "PageCompiler": PageCompiler,
            "TaskMultiplier": TaskMultiplier,
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
            if plugin_info.name in self.config["post_compilers"].keys():
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)

        # set global_context for template rendering
        self.GLOBAL_CONTEXT = {
        }

        self.GLOBAL_CONTEXT['messages'] = self.MESSAGES
        self.GLOBAL_CONTEXT['_link'] = self.link
        self.GLOBAL_CONTEXT['set_locale'] = s_l
        self.GLOBAL_CONTEXT['rel_link'] = self.rel_link
        self.GLOBAL_CONTEXT['abs_link'] = self.abs_link
        self.GLOBAL_CONTEXT['exists'] = self.file_exists
        self.GLOBAL_CONTEXT['SLUG_TAG_PATH'] = self.config[
            'SLUG_TAG_PATH']

        self.GLOBAL_CONTEXT['add_this_buttons'] = self.config[
            'ADD_THIS_BUTTONS']
        self.GLOBAL_CONTEXT['index_display_post_count'] = self.config[
            'INDEX_DISPLAY_POST_COUNT']
        self.GLOBAL_CONTEXT['use_bundles'] = self.config['USE_BUNDLES']
        self.GLOBAL_CONTEXT['use_cdn'] = self.config.get("USE_CDN")
        self.GLOBAL_CONTEXT['favicons'] = self.config['FAVICONS']
        self.GLOBAL_CONTEXT['date_format'] = self.config.get(
            'DATE_FORMAT', '%Y-%m-%d %H:%M')
        self.GLOBAL_CONTEXT['blog_author'] = self.config.get('BLOG_AUTHOR')
        self.GLOBAL_CONTEXT['blog_title'] = self.config.get('BLOG_TITLE')

        self.GLOBAL_CONTEXT['blog_url'] = self.config.get('SITE_URL', self.config.get('BLOG_URL'))
        self.GLOBAL_CONTEXT['blog_desc'] = self.config.get('BLOG_DESCRIPTION')
        self.GLOBAL_CONTEXT['analytics'] = self.config.get('ANALYTICS')
        self.GLOBAL_CONTEXT['translations'] = self.config.get('TRANSLATIONS')
        self.GLOBAL_CONTEXT['license'] = self.config.get('LICENSE')
        self.GLOBAL_CONTEXT['search_form'] = self.config.get('SEARCH_FORM')
        self.GLOBAL_CONTEXT['disqus_forum'] = self.config.get('DISQUS_FORUM')
        self.GLOBAL_CONTEXT['mathjax_config'] = self.config.get(
            'MATHJAX_CONFIG')
        self.GLOBAL_CONTEXT['subtheme'] = self.config.get('THEME_REVEAL_CONGIF_SUBTHEME')
        self.GLOBAL_CONTEXT['transition'] = self.config.get('THEME_REVEAL_CONGIF_TRANSITION')
        self.GLOBAL_CONTEXT['content_footer'] = self.config.get(
            'CONTENT_FOOTER')
        self.GLOBAL_CONTEXT['rss_path'] = self.config.get('RSS_PATH')
        self.GLOBAL_CONTEXT['rss_link'] = self.config.get('RSS_LINK')

        self.GLOBAL_CONTEXT['sidebar_links'] = utils.Functionary(list, self.config['DEFAULT_LANG'])
        for k, v in self.config.get('SIDEBAR_LINKS', {}).items():
            self.GLOBAL_CONTEXT['sidebar_links'][k] = v

        self.GLOBAL_CONTEXT['twitter_card'] = self.config.get(
            'TWITTER_CARD', {})
        self.GLOBAL_CONTEXT['extra_head_data'] = self.config.get('EXTRA_HEAD_DATA')

        self.GLOBAL_CONTEXT.update(self.config.get('GLOBAL_CONTEXT', {}))

        # check if custom css exist and is not empty
        for files_path in list(self.config['FILES_FOLDERS'].keys()):
            custom_css_path = os.path.join(files_path, 'assets/css/custom.css')
            if self.file_exists(custom_css_path, not_empty=True):
                self.GLOBAL_CONTEXT['has_custom_css'] = True
                break
        else:
            self.GLOBAL_CONTEXT['has_custom_css'] = False

        # Load template plugin
        template_sys_name = utils.get_template_engine(self.THEMES)
        pi = self.plugin_manager.getPluginByName(
            template_sys_name, "TemplateSystem")
        if pi is None:
            sys.stderr.write("Error loading {0} template system "
                             "plugin\n".format(template_sys_name))
            sys.exit(1)
        self.template_system = pi.plugin_object
        lookup_dirs = ['templates'] + [os.path.join(utils.get_theme_path(name), "templates")
                                       for name in self.THEMES]
        self.template_system.set_directories(lookup_dirs,
                                             self.config['CACHE_FOLDER'])

        # Check consistency of USE_CDN and the current THEME (Issue #386)
        if self.config['USE_CDN']:
            bootstrap_path = utils.get_asset_path(os.path.join(
                'assets', 'css', 'bootstrap.min.css'), self.THEMES)
            if bootstrap_path.split(os.sep)[-4] != 'site':
                warnings.warn('The USE_CDN option may be incompatible with your theme, because it uses a hosted version of bootstrap.')

        # Load compiler plugins
        self.compilers = {}
        self.inverse_compilers = {}

        for plugin_info in self.plugin_manager.getPluginsOfCategory(
                "PageCompiler"):
            self.compilers[plugin_info.name] = \
                plugin_info.plugin_object

    def get_compiler(self, source_name):
        """Get the correct compiler for a post from `conf.post_compilers`

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
                     list(self.config['post_compilers'].items())
                     if ext in exts]
            if len(langs) != 1:
                if len(set(langs)) > 1:
                    exit("Your file extension->compiler definition is"
                         "ambiguous.\nPlease remove one of the file extensions"
                         "from 'post_compilers' in conf.py\n(The error is in"
                         "one of {0})".format(', '.join(langs)))
                elif len(langs) > 1:
                    langs = langs[:1]
                else:
                    exit("post_compilers in conf.py does not tell me how to "
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
                return "#"
            # Check that link can be made relative, otherwise return dest
            parsed_dst = urlsplit(dst)
            if parsed_src[:2] != parsed_dst[:2]:
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

        try:
            os.makedirs(os.path.dirname(output_name))
        except:
            pass
        doc = lxml.html.document_fromstring(data)
        doc.rewrite_links(replacer)
        data = b'<!DOCTYPE html>' + lxml.html.tostring(doc, encoding='utf8')
        with open(output_name, "wb+") as post_file:
            post_file.write(data)

    def current_lang(self):  # FIXME: this is duplicated, turn into a mixin
        """Return the currently set locale, if it's one of the
        available translations, or default_lang."""
        lang = utils.LocaleBorg().current_lang
        if lang:
            if lang in self.translations:
                return lang
            lang = lang.split('_')[0]
            if lang in self.translations:
                return lang
        # whatever
        return self.default_lang

    def path(self, kind, name, lang=None, is_link=False):
        """Build the path to a certain kind of page.

        kind is one of:

        * tag_index (name is ignored)
        * tag (and name is the tag name)
        * tag_rss (name is the tag name)
        * archive (and name is the year, or None for the main archive index)
        * index (name is the number in index-number)
        * rss (name is ignored)
        * gallery (name is the gallery name)
        * listing (name is the source code file name)
        * post_path (name is 1st element in a post_pages tuple)

        The returned value is always a path relative to output, like
        "categories/whatever.html"

        If is_link is True, the path is absolute and uses "/" as separator
        (ex: "/archive/index.html").
        If is_link is False, the path is relative to output and uses the
        platform's separator.
        (ex: "archive\\index.html")
        """

        if lang is None:
            lang = self.current_lang()

        path = []

        if kind == "tag_index":
            path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                  self.config['TAG_PATH'],
                                  self.config['INDEX_FILE']] if _f]
        elif kind == "tag":
            if self.config['SLUG_TAG_PATH']:
                name = utils.slugify(name)
            path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                  self.config['TAG_PATH'], name + ".html"] if
                    _f]
        elif kind == "tag_rss":
            if self.config['SLUG_TAG_PATH']:
                name = utils.slugify(name)
            path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                  self.config['TAG_PATH'], name + ".xml"] if
                    _f]
        elif kind == "index":
            if name not in [None, 0]:
                path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                      self.config['INDEX_PATH'],
                                      'index-{0}.html'.format(name)] if _f]
            else:
                path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                      self.config['INDEX_PATH'],
                                      self.config['INDEX_FILE']]
                        if _f]
        elif kind == "post_path":
            path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                  os.path.dirname(name),
                                  self.config['INDEX_FILE']] if _f]
        elif kind == "rss":
            path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                  self.config['RSS_PATH'], 'rss.xml'] if _f]
        elif kind == "archive":
            if name:
                path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                      self.config['ARCHIVE_PATH'], name,
                                      self.config['INDEX_FILE']] if _f]
            else:
                path = [_f for _f in [self.config['TRANSLATIONS'][lang],
                                      self.config['ARCHIVE_PATH'],
                                      self.config['ARCHIVE_FILENAME']] if _f]
        elif kind == "gallery":
            path = [_f for _f in [self.config['GALLERY_PATH'], name,
                                  self.config['INDEX_FILE']] if _f]
        elif kind == "listing":
            path = [_f for _f in [self.config['LISTINGS_FOLDER'], name +
                                  '.html'] if _f]
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

    def gen_tasks(self, name, plugin_category):

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
                yield task
                for multi in self.plugin_manager.getPluginsOfCategory("TaskMultiplier"):
                    flag = False
                    for task in multi.plugin_object.process(task, name):
                        flag = True
                        yield task
                    if flag:
                        task_dep.append('{0}_{1}'.format(name, multi.plugin_object.name))
            if pluginInfo.plugin_object.is_default:
                task_dep.append(pluginInfo.plugin_object.name)
        yield {
            'name': name,
            'actions': None,
            'clean': True,
            'task_dep': task_dep
        }

    def scan_posts(self):
        """Scan all the posts."""
        if self._scanned:
            return

        print("Scanning posts", end='')
        tzinfo = None
        if self.config['TIMEZONE'] is not None:
            tzinfo = pytz.timezone(self.config['TIMEZONE'])
        current_time = utils.current_time(tzinfo)
        targets = set([])
        for wildcard, destination, template_name, use_in_feeds in \
                self.config['post_pages']:
            print(".", end='')
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

                for base_path in full_list:
                    post = Post(
                        base_path,
                        self.config['CACHE_FOLDER'],
                        dest_dir,
                        use_in_feeds,
                        self.config['TRANSLATIONS'],
                        self.config['DEFAULT_LANG'],
                        self.config['BASE_URL'],
                        self.MESSAGES,
                        template_name,
                        self.config['FILE_METADATA_REGEXP'],
                        self.config['STRIP_INDEXES'],
                        self.config['INDEX_FILE'],
                        tzinfo,
                        current_time,
                        self.config['HIDE_UNTRANSLATED_POSTS'],
                        self.config['PRETTY_URLS'],
                    )
                    for lang, langpath in list(
                            self.config['TRANSLATIONS'].items()):
                        dest = (destination, langpath, dir_glob,
                                post.meta[lang]['slug'])
                        if dest in targets:
                            raise Exception('Duplicated output path {0!r} '
                                            'in post {1!r}'.format(
                                                post.meta[lang]['slug'],
                                                base_path))
                        targets.add(dest)
                    self.global_data[post.post_name] = post
                    if post.use_in_feeds:
                        self.posts_per_year[
                            str(post.date.year)].append(post.post_name)
                        self.posts_per_month[
                            '{0}/{1:02d}'.format(post.date.year, post.date.month)].append(post.post_name)
                        for tag in post.alltags:
                            self.posts_per_tag[tag].append(post.post_name)
                    else:
                        self.pages.append(post)
                    if self.config['OLD_THEME_SUPPORT']:
                        post._add_old_metadata()
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
        print("done!")

    def generic_page_renderer(self, lang, post, filters):
        """Render post fragments to final HTML pages."""
        context = {}
        deps = post.deps(lang) + \
            self.template_system.template_deps(post.template_name)
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


def s_l(lang):
    """A set_locale that uses utf8 encoding and returns ''."""
    utils.LocaleBorg().current_lang = lang
    try:
        locale.setlocale(locale.LC_ALL, (lang, "utf8"))
    except Exception:
        print("WARNING: could not set locale to {0}."
              "This may cause some i18n features not to work.".format(lang))
    return ''
