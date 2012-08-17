# -*- coding: utf-8 -*-

import codecs
from collections import defaultdict
from copy import copy
import datetime
import glob
import json
import os
from StringIO import StringIO
import sys
import tempfile
import urllib2
import urlparse

from doit.tools import PythonInteractiveAction
import lxml.html
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
try:
    import webassets
except ImportError:
    webassets = None

import utils

config_changed = utils.config_changed

__all__ = ['Nikola', 'nikola_main']


class Post(object):

    """Represents a blog post or web page."""

    def __init__(self, source_path, destination, use_in_feeds,
        translations, default_lang, blog_url, compile_html):
        """Initialize post.

        The base path is the .txt post file. From it we calculate
        the meta file, as well as any translations available, and
        the .html fragment file path.

        `compile_html` is a function that knows how to compile this Post to
        html.
        """
        self.prev_post = None
        self.next_post = None
        self.blog_url = blog_url
        self.is_draft = False
        self.source_path = source_path  # posts/blah.txt
        self.post_name = os.path.splitext(source_path)[0]  # posts/blah
        # cache/posts/blah.html
        self.base_path = os.path.join('cache', self.post_name + ".html")
        self.metadata_path = self.post_name + ".meta"  # posts/blah.meta
        self.folder = destination
        self.translations = translations
        self.default_lang = default_lang
        if os.path.isfile(self.metadata_path):
            with codecs.open(self.metadata_path, "r", "utf8") as meta_file:
                meta_data = meta_file.readlines()
            while len(meta_data) < 6:
                meta_data.append("")
            default_title, default_pagename, self.date, self.tags, self.link, default_description = \
                [x.strip() for x in meta_data][:6]
        else:
            default_title, default_pagename, self.date, self.tags, self.link, default_description = \
                utils.get_meta(self.source_path)

        if not default_title or not default_pagename or not self.date:
            raise OSError("You must set a title and slug and date!")

        self.date = utils.to_datetime(self.date)
        self.tags = [x.strip() for x in self.tags.split(',')]
        self.tags = filter(None, self.tags)

        # While draft comes from the tags, it's not really a tag
        self.use_in_feeds = use_in_feeds and "draft" not in self.tags
        self.is_draft = 'draft' in self.tags
        self.tags = [t for t in self.tags if t != 'draft']

        self.compile_html = compile_html

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
                            self.descriptions[lang] = meta_data[5] or default_description
                    else:
                        ttitle, ppagename, tmp1, tmp2, tmp3, ddescription = \
                            utils.get_meta(source_path)
                        self.titles[lang] = ttitle or default_title
                        self.pagenames[lang] = ppagename or default_pagename
                        self.descriptions[lang] = ddescription or default_description
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
            lang_deps = filter(os.path.exists, [x + "." + lang for x in deps])
            deps += lang_deps
        return deps

    def text(self, lang, teaser_only=False):
        """Read the post file for that language and return its contents"""
        file_name = self.base_path
        if lang != self.default_lang:
            file_name_lang = file_name + ".%s" % lang
            if os.path.exists(file_name_lang):
                file_name = file_name_lang
        with codecs.open(file_name, "r", "utf8") as post_file:
            data = post_file.read()

        data = lxml.html.make_links_absolute(data, self.permalink())
        if teaser_only:
            e = lxml.html.fromstring(data)
            teaser = []
            flag = False
            for elem in e:
                elem_string = lxml.html.tostring(elem)
                if '<!-- TEASER_END -->' in elem_string.upper():
                    flag = True
                    break
                teaser.append(elem_string)
            if flag:
                teaser.append('<p><a href="%s">Read more...</a></p>' %
                    self.permalink(lang))
            data = ''.join(teaser)
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
        pieces = filter(None, pieces)
        if absolute:
            pieces = [self.blog_url] + pieces
        else:
            pieces = [""] + pieces
        link = "/".join(pieces)
        return link

    def source_ext(self):
        return os.path.splitext(self.source_path)[1]


class Nikola(object):

    """Class that handles site generation.

    Takes a site config as argument on creation.
    """

    def __init__(self, **config):
        """Setup proper environment for running tasks."""

        self.global_data = {}
        self.posts_per_year = defaultdict(list)
        self.posts_per_tag = defaultdict(list)
        self.timeline = []
        self.pages = []
        self._scanned = False

        # This is the default config
        # TODO: fill it
        self.config = {
            'ARCHIVE_PATH': "",
            'ARCHIVE_FILENAME': "archive.html",
            'OUTPUT_FOLDER': 'output',
            'FILES_FOLDERS': {'files': ''},
            'LISTINGS_FOLDER': 'listings',
            'ADD_THIS_BUTTONS': True,
            'INDEX_DISPLAY_POST_COUNT': 10,
            'INDEX_TEASERS': False,
            'MAX_IMAGE_SIZE': 1280,
            'USE_FILENAME_AS_TITLE': True,
            'SLUG_TAG_PATH': False,
            'INDEXES_TITLE': "",
            'INDEXES_PAGES': "",
            'FILTERS': {},
            'USE_BUNDLES': True,
            'post_compilers': {
                "rest":     ['.txt', '.rst'],
                "markdown": ['.md', '.mdown', '.markdown'],
                "html": ['.html', '.htm'],
            },
        }
        self.config.update(config)

        if self.config['USE_BUNDLES'] and not webassets:
            print "You have enabled USE_BUNDLES but webassets is not installed."

        self.get_compile_html = utils.CompileHtmlGetter(
            self.config.pop('post_compilers'))

        self.GLOBAL_CONTEXT = self.config['GLOBAL_CONTEXT']
        self.THEMES = utils.get_theme_chain(self.config['THEME'])

        self.templates_module = utils.get_template_module(
            utils.get_template_engine(self.THEMES), self.THEMES)
        self.template_deps = self.templates_module.template_deps

        self.theme_bundles = utils.get_theme_bundles(self.THEMES)

        self.MESSAGES = utils.load_messages(self.THEMES,
            self.config['TRANSLATIONS'])
        self.GLOBAL_CONTEXT['messages'] = self.MESSAGES

        self.GLOBAL_CONTEXT['_link'] = self.link
        self.GLOBAL_CONTEXT['rel_link'] = self.rel_link
        self.GLOBAL_CONTEXT['abs_link'] = self.abs_link
        self.GLOBAL_CONTEXT['exists'] = self.file_exists
        self.GLOBAL_CONTEXT['add_this_buttons'] = self.config[
            'ADD_THIS_BUTTONS']
        self.GLOBAL_CONTEXT['index_display_post_count'] = self.config[
            'INDEX_DISPLAY_POST_COUNT']
        self.GLOBAL_CONTEXT['use_bundles'] = self.config['USE_BUNDLES']

        self.DEPS_CONTEXT = {}
        for k, v in self.GLOBAL_CONTEXT.items():
            if isinstance(v, (str, unicode, int, float, dict)):
                self.DEPS_CONTEXT[k] = v

    def render_template(self, template_name, output_name, context):
        data = self.templates_module.render_template(
            template_name, None, context, self.GLOBAL_CONTEXT)

        assert output_name.startswith(self.config["OUTPUT_FOLDER"])
        url_part = output_name[len(self.config["OUTPUT_FOLDER"]) + 1:]

        #this to support windows paths
        url_part = "/".join(url_part.split(os.sep))

        src = urlparse.urljoin(self.config["BLOG_URL"], url_part)

        parsed_src = urlparse.urlsplit(src)
        src_elems = parsed_src.path.split('/')[1:]

        def replacer(dst):
            # Refuse to replace links that are full URLs.
            dst_url = urlparse.urlparse(dst)
            if dst_url.netloc:
                if dst_url.scheme == 'link':  # Magic link
                    dst = self.link(dst_url.netloc, dst_url.path.lstrip('/'),
                        context['lang'])
                else:
                    return dst

            # Normalize
            dst = urlparse.urljoin(src, dst)
            # Avoid empty links.
            if src == dst:
                return "#"
            # Check that link can be made relative, otherwise return dest
            parsed_dst = urlparse.urlsplit(dst)
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
        data = '<!DOCTYPE html>' + lxml.html.tostring(doc, encoding='utf8')
        with open(output_name, "w+") as post_file:
            post_file.write(data)

    def path(self, kind, name, lang, is_link=False):
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

        The returned value is always a path relative to output, like
        "categories/whatever.html"

        If is_link is True, the path is absolute and uses "/" as separator
        (ex: "/archive/index.html").
        If is_link is False, the path is relative to output and uses the
        platform's separator.
        (ex: "archive\\index.html")
        """

        path = []

        if kind == "tag_index":
            path = filter(None, [self.config['TRANSLATIONS'][lang],
            self.config['TAG_PATH'], 'index.html'])
        elif kind == "tag":
            if self.config['SLUG_TAG_PATH']:
                name = utils.slugify(name)
            path = filter(None, [self.config['TRANSLATIONS'][lang],
            self.config['TAG_PATH'], name + ".html"])
        elif kind == "tag_rss":
            if self.config['SLUG_TAG_PATH']:
                name = utils.slugify(name)
            path = filter(None, [self.config['TRANSLATIONS'][lang],
            self.config['TAG_PATH'], name + ".xml"])
        elif kind == "index":
            if name > 0:
                path = filter(None, [self.config['TRANSLATIONS'][lang],
                self.config['INDEX_PATH'], 'index-%s.html' % name])
            else:
                path = filter(None, [self.config['TRANSLATIONS'][lang],
                self.config['INDEX_PATH'], 'index.html'])
        elif kind == "rss":
            path = filter(None, [self.config['TRANSLATIONS'][lang],
            self.config['RSS_PATH'], 'rss.xml'])
        elif kind == "archive":
            if name:
                path = filter(None, [self.config['TRANSLATIONS'][lang],
                self.config['ARCHIVE_PATH'], name, 'index.html'])
            else:
                path = filter(None, [self.config['TRANSLATIONS'][lang],
                self.config['ARCHIVE_PATH'], self.config['ARCHIVE_FILENAME']])
        elif kind == "gallery":
            path = filter(None,
                [self.config['GALLERY_PATH'], name, 'index.html'])
        elif kind == "listing":
            path = filter(None,
                [self.config['LISTINGS_FOLDER'], name + '.html'])
        if is_link:
            return '/' + ('/'.join(path))
        else:
            return os.path.join(*path)

    def link(self, *args):
        return self.path(*args, is_link=True)

    def abs_link(self, dst):
        # Normalize
        dst = urlparse.urljoin(self.config['BLOG_URL'], dst)

        return urlparse.urlparse(dst).path

    def rel_link(self, src, dst):
        # Normalize
        src = urlparse.urljoin(self.config['BLOG_URL'], src)
        dst = urlparse.urljoin(src, dst)
        # Avoid empty links.
        if src == dst:
            return "#"
        # Check that link can be made relative, otherwise return dest
        parsed_src = urlparse.urlsplit(src)
        parsed_dst = urlparse.urlsplit(dst)
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

    def gen_tasks(self):

        yield self.task_serve(output_folder=self.config['OUTPUT_FOLDER'])
        yield self.task_install_theme()
        yield self.task_bootswatch_theme()
        yield self.gen_task_new_post(self.config['post_pages'])
        yield self.gen_task_new_page(self.config['post_pages'])
        yield self.gen_task_copy_assets(themes=self.THEMES,
            output_folder=self.config['OUTPUT_FOLDER'],
            filters=self.config['FILTERS']
        )
        if webassets:
            yield self.gen_task_build_bundles(theme_bundles=self.theme_bundles,
                output_folder=self.config['OUTPUT_FOLDER'],
                filters=self.config['FILTERS']
            )
        yield self.gen_task_deploy(commands=self.config['DEPLOY_COMMANDS'])
        yield self.gen_task_sitemap(blog_url=self.config['BLOG_URL'],
            output_folder=self.config['OUTPUT_FOLDER']
        )
        yield self.gen_task_render_pages(
            translations=self.config['TRANSLATIONS'],
            post_pages=self.config['post_pages'],
            filters=self.config['FILTERS'])
        yield self.gen_task_render_sources(
            translations=self.config['TRANSLATIONS'],
            default_lang=self.config['DEFAULT_LANG'],
            output_folder=self.config['OUTPUT_FOLDER'],
            post_pages=self.config['post_pages'])
        yield self.gen_task_render_posts(
            translations=self.config['TRANSLATIONS'],
            default_lang=self.config['DEFAULT_LANG'],
            timeline=self.timeline
            )
        yield self.gen_task_render_indexes(
            translations=self.config['TRANSLATIONS'],
            messages=self.MESSAGES,
            output_folder=self.config['OUTPUT_FOLDER'],
            index_display_post_count=self.config['INDEX_DISPLAY_POST_COUNT'],
            index_teasers=self.config['INDEX_TEASERS'],
            filters=self.config['FILTERS'],
        )
        yield self.gen_task_render_archive(
            translations=self.config['TRANSLATIONS'],
            messages=self.MESSAGES,
            output_folder=self.config['OUTPUT_FOLDER'],
            filters=self.config['FILTERS'],
        )
        yield self.gen_task_render_tags(
            translations=self.config['TRANSLATIONS'],
            messages=self.MESSAGES,
            blog_title=self.config['BLOG_TITLE'],
            blog_url=self.config['BLOG_URL'],
            blog_description=self.config['BLOG_DESCRIPTION'],
            output_folder=self.config['OUTPUT_FOLDER'],
            filters=self.config['FILTERS']
        )
        yield self.gen_task_render_rss(
            translations=self.config['TRANSLATIONS'],
            blog_title=self.config['BLOG_TITLE'],
            blog_url=self.config['BLOG_URL'],
            blog_description=self.config['BLOG_DESCRIPTION'],
            output_folder=self.config['OUTPUT_FOLDER'])
        yield self.gen_task_render_galleries(
            max_image_size=self.config['MAX_IMAGE_SIZE'],
            thumbnail_size=self.config['THUMBNAIL_SIZE'],
            default_lang=self.config['DEFAULT_LANG'],
            output_folder=self.config['OUTPUT_FOLDER'],
            use_filename_as_title=self.config['USE_FILENAME_AS_TITLE'],
            blog_description=self.config['BLOG_DESCRIPTION']
        )
        yield self.gen_task_render_listings(
            listings_folder=self.config['LISTINGS_FOLDER'],
            default_lang=self.config['DEFAULT_LANG'],
            output_folder=self.config['OUTPUT_FOLDER'])
        yield self.gen_task_redirect(
            redirections=self.config['REDIRECTIONS'],
            output_folder=self.config['OUTPUT_FOLDER'])
        yield self.gen_task_copy_files(
            output_folder=self.config['OUTPUT_FOLDER'],
            files_folders=self.config['FILES_FOLDERS'],
            filters=self.config['FILTERS'])

        task_dep = [
                'render_listings',
                'render_archive',
                'render_galleries',
                'render_indexes',
                'render_pages',
                'render_posts',
                'render_rss',
                'render_sources',
                'render_tags',
                'copy_assets',
                'copy_files',
                'sitemap',
                'redirect'
        ]

        if webassets:
            task_dep.append( 'build_bundles' )

        yield {
            'name': 'all',
            'actions': None,
            'clean': True,
            'task_dep': task_dep
         }

    def scan_posts(self):
        """Scan all the posts."""
        if not self._scanned:
            print "Scanning posts ",
            targets = set([])
            for wildcard, destination, _, use_in_feeds in self.config['post_pages']:
                print ".",
                for base_path in glob.glob(wildcard):
                    post = Post(base_path, destination, use_in_feeds,
                        self.config['TRANSLATIONS'],
                        self.config['DEFAULT_LANG'],
                        self.config['BLOG_URL'],
                        self.get_compile_html(base_path))
                    for lang, langpath in self.config['TRANSLATIONS'].items():
                        dest = (destination, langpath, post.pagenames[lang])
                        if dest in targets:
                            raise Exception(
                                'Duplicated output path %r in post %r' %
                                (post.pagenames[lang], base_path))
                        targets.add(dest)
                    self.global_data[post.post_name] = post
                    if post.use_in_feeds:
                        self.posts_per_year[
                            str(post.date.year)].append(post.post_name)
                        for tag in post.tags:
                            self.posts_per_tag[tag].append(post.post_name)
                    else:
                        self.pages.append(post)
            for name, post in self.global_data.items():
                self.timeline.append(post)
            self.timeline.sort(cmp=lambda a, b: cmp(a.date, b.date))
            self.timeline.reverse()
            post_timeline = [p for p in self.timeline if p.use_in_feeds]
            for i, p in enumerate(post_timeline[1:]):
                p.next_post = post_timeline[i]
            for i, p in enumerate(post_timeline[:-1]):
                p.prev_post = post_timeline[i + 1]
            self._scanned = True
            print "done!"

    def generic_page_renderer(self, lang, wildcard,
        template_name, destination, filters):
        """Render post fragments to final HTML pages."""
        for post in glob.glob(wildcard):
            post_name = os.path.splitext(post)[0]
            context = {}
            post = self.global_data[post_name]
            deps = post.deps(lang) + self.template_deps(template_name)
            context['post'] = post
            context['lang'] = lang
            context['title'] = post.title(lang)
            context['description'] = post.description(lang)
            context['permalink'] = post.permalink(lang)
            context['page_list'] = self.pages
            output_name = os.path.join(
                self.config['OUTPUT_FOLDER'],
                self.config['TRANSLATIONS'][lang],
                destination,
                post.pagenames[lang] + ".html")
            deps_dict = copy(context)
            deps_dict.pop('post')
            if post.prev_post:
                deps_dict['PREV_LINK'] = [post.prev_post.permalink(lang)]
            if post.next_post:
                deps_dict['NEXT_LINK'] = [post.next_post.permalink(lang)]
            deps_dict['OUTPUT_FOLDER'] = self.config['OUTPUT_FOLDER']
            deps_dict['TRANSLATIONS'] = self.config['TRANSLATIONS']

            task = {
                'name': output_name.encode('utf-8'),
                'file_dep': deps,
                'targets': [output_name],
                'actions': [(self.render_template,
                    [template_name, output_name, context])],
                'clean': True,
                'uptodate': [config_changed(deps_dict)],
            }

            yield utils.apply_filters(task, filters)

    def gen_task_render_pages(self, **kw):
        """Build final pages from metadata and HTML fragments.

        Required keyword arguments:

        translations
        post_pages
        """
        self.scan_posts()
        for lang in kw["translations"]:
            for wildcard, destination, template_name, _ in kw["post_pages"]:
                for task in self.generic_page_renderer(lang,
                    wildcard, template_name, destination, kw["filters"]):
                    # TODO: enable or remove
                    #task['uptodate'] = task.get('uptodate', []) +\
                        #[config_changed(kw)]
                    task['basename'] = 'render_pages'
                    yield task

    def gen_task_render_sources(self, **kw):
        """Publish the rst sources because why not?

        Required keyword arguments:

        translations
        default_lang
        post_pages
        output_folder
        """
        self.scan_posts()
        for lang in kw["translations"]:
            # TODO: timeline is global
            for post in self.timeline:
                output_name = os.path.join(kw['output_folder'],
                    post.destination_path(lang, post.source_ext()))
                source = post.source_path
                if lang != kw["default_lang"]:
                    source_lang = source + '.' + lang
                    if os.path.exists(source_lang):
                        source = source_lang
                yield {
                    'basename': 'render_sources',
                    'name': output_name.encode('utf8'),
                    'file_dep': [source],
                    'targets': [output_name],
                    'actions': [(utils.copy_file, (source, output_name))],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                    }

    def gen_task_render_posts(self, **kw):
        """Build HTML fragments from metadata and reSt.

        Required keyword arguments:

        translations
        default_lang
        timeline
        """
        self.scan_posts()
        for lang in kw["translations"]:
            # TODO: timeline is global, get rid of it
            deps_dict = copy(kw)
            deps_dict.pop('timeline')
            for post in kw['timeline']:
                source = post.source_path
                dest = post.base_path
                if lang != kw["default_lang"]:
                    dest += '.' + lang
                    source_lang = source + '.' + lang
                    if os.path.exists(source_lang):
                        source = source_lang
                yield {
                    'basename': 'render_posts',
                    'name': dest.encode('utf-8'),
                    'file_dep': post.fragment_deps(lang),
                    'targets': [dest],
                    'actions': [(post.compile_html, [source, dest])],
                    'clean': True,
                    'uptodate': [config_changed(deps_dict)],
                }

    def gen_task_render_indexes(self, **kw):
        """Render post-per-page indexes.
        The default is 10.

        Required keyword arguments:

        translations
        output_folder
        index_display_post_count
        index_teasers
        """
        self.scan_posts()
        template_name = "index.tmpl"
        # TODO: timeline is global, get rid of it
        posts = [x for x in self.timeline if x.use_in_feeds]
        # Split in smaller lists
        lists = []
        while posts:
            lists.append(posts[:kw["index_display_post_count"]])
            posts = posts[kw["index_display_post_count"]:]
        num_pages = len(lists)
        if not lists:
            yield {
                'basename': 'render_indexes',
                'actions': [],
                }
        for lang in kw["translations"]:
            for i, post_list in enumerate(lists):
                context = {}
                if self.config.get("INDEXES_TITLE", ""):
                    indexes_title = self.config['INDEXES_TITLE']
                else:
                    indexes_title = self.config["BLOG_TITLE"]
                if not i:
                    output_name = "index.html"
                    context["title"] = indexes_title
                else:
                    output_name = "index-%s.html" % i
                    if self.config.get("INDEXES_PAGES", ""):
                        indexes_pages = self.config["INDEXES_PAGES"] % i
                    else:
                        indexes_pages = " (" + kw["messages"][lang]["old posts page %d"] % i + ")"
                    context["title"] = indexes_title + indexes_pages
                context["prevlink"] = None
                context["nextlink"] = None
                context['index_teasers'] = kw['index_teasers']
                if i > 1:
                    context["prevlink"] = "index-%s.html" % (i - 1)
                if i == 1:
                    context["prevlink"] = "index.html"
                if i < num_pages - 1:
                    context["nextlink"] = "index-%s.html" % (i + 1)
                context["permalink"] = self.link("index", i, lang)
                output_name = os.path.join(
                    kw['output_folder'], self.path("index", i, lang))
                for task in self.generic_post_list_renderer(
                    lang,
                    post_list,
                    output_name,
                    template_name,
                    kw['filters'],
                    context,
                ):
                    task['uptodate'] = task.get('updtodate', []) +\
                                    [config_changed(kw)]
                    task['basename'] = 'render_indexes'
                    yield task

    def generic_post_list_renderer(self, lang, posts,
        output_name, template_name, filters, extra_context):
        """Renders pages with lists of posts."""

        deps = self.template_deps(template_name)
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
        deps_context["posts"] = [(p.titles[lang], p.permalink(lang))
            for p in posts]
        task = {
            'name': output_name.encode('utf8'),
            'targets': [output_name],
            'file_dep': deps,
            'actions': [(self.render_template,
                [template_name, output_name, context])],
            'clean': True,
            'uptodate': [config_changed(deps_context)]
        }

        yield utils.apply_filters(task, filters)

    def gen_task_render_archive(self, **kw):
        """Render the post archives.

        Required keyword arguments:

        translations
        messages
        output_folder
        """
        # TODO add next/prev links for years
        template_name = "list.tmpl"
        # TODO: posts_per_year is global, kill it
        for year, posts in self.posts_per_year.items():
            for lang in kw["translations"]:
                output_name = os.path.join(
                    kw['output_folder'], self.path("archive", year, lang))
                post_list = [self.global_data[post] for post in posts]
                post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
                post_list.reverse()
                context = {}
                context["lang"] = lang
                context["items"] = [("[%s] %s" %
                    (post.date, post.title(lang)), post.permalink(lang))
                    for post in post_list]
                context["permalink"] = self.link("archive", year, lang)
                context["title"] = kw["messages"][lang]["Posts for year %s"]\
                    % year
                for task in self.generic_post_list_renderer(
                    lang,
                    post_list,
                    output_name,
                    template_name,
                    kw['filters'],
                    context,
                ):
                    task['uptodate'] = task.get('updtodate', []) +\
                                       [config_changed(kw)]
                    yield task

        # And global "all your years" page
        years = self.posts_per_year.keys()
        years.sort(reverse=True)
        template_name = "list.tmpl"
        kw['years'] = years
        for lang in kw["translations"]:
            context = {}
            output_name = os.path.join(
                kw['output_folder'], self.path("archive", None, lang))
            context["title"] = kw["messages"][lang]["Archive"]
            context["items"] = [(year, self.link("archive", year, lang))
                for year in years]
            context["permalink"] = self.link("archive", None, lang)
            for task in self.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            ):
                task['uptodate'] = task.get('updtodate', []) +\
                    [config_changed(kw)]
                task['basename'] = 'render_archive'
                yield task

    def gen_task_render_tags(self, **kw):
        """Render the tag pages.

        Required keyword arguments:

        translations
        messages
        blog_title
        blog_url
        blog_description
        output_folder
        """
        template_name = "tag.tmpl"
        if not self.posts_per_tag:
            yield {
                    'basename': 'render_tags',
                    'actions': [],
                }
            return
        for tag, posts in self.posts_per_tag.items():
            for lang in kw["translations"]:
                # Render HTML
                output_name = os.path.join(kw['output_folder'],
                    self.path("tag", tag, lang))
                post_list = [self.global_data[post] for post in posts]
                post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
                post_list.reverse()
                context = {}
                context["lang"] = lang
                context["title"] = kw["messages"][lang][u"Posts about %s:"]\
                    % tag
                context["items"] = [("[%s] %s" % (post.date, post.title(lang)),
                    post.permalink(lang)) for post in post_list]
                context["permalink"] = self.link("tag", tag, lang)
                context["tag"] = tag

                for task in self.generic_post_list_renderer(
                    lang,
                    post_list,
                    output_name,
                    template_name,
                    kw['filters'],
                    context,
                ):
                    task['uptodate'] = task.get('updtodate', []) +\
                                       [config_changed(kw)]
                    task['basename'] = 'render_tags'
                    yield task

                #Render RSS
                output_name = os.path.join(kw['output_folder'],
                    self.path("tag_rss", tag, lang))
                deps = []
                post_list = [self.global_data[post] for post in posts
                    if self.global_data[post].use_in_feeds]
                post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
                post_list.reverse()
                for post in post_list:
                    deps += post.deps(lang)
                yield {
                    'name': output_name.encode('utf8'),
                    'file_dep': deps,
                    'targets': [output_name],
                    'actions': [(utils.generic_rss_renderer,
                        (lang, "%s (%s)" % (kw["blog_title"], tag),
                        kw["blog_url"], kw["blog_description"],
                        post_list, output_name))],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                }

        # And global "all your tags" page
        tags = self.posts_per_tag.keys()
        tags.sort()
        template_name = "tags.tmpl"
        kw['tags'] = tags
        for lang in kw["translations"]:
            output_name = os.path.join(
                kw['output_folder'], self.path('tag_index', None, lang))
            context = {}
            context["title"] = kw["messages"][lang][u"Tags"]
            context["items"] = [(tag, self.link("tag", tag, lang))
                for tag in tags]
            context["permalink"] = self.link("tag_index", None, lang)
            for task in self.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            ):
                task['uptodate'] = task.get('updtodate', []) +\
                    [config_changed(kw)]
                yield task

    def gen_task_render_rss(self, **kw):
        """Generate RSS feeds.

        Required keyword arguments:

        translations
        blog_title
        blog_url
        blog_description
        output_folder
        """

        self.scan_posts()
        # TODO: timeline is global, kill it
        for lang in kw["translations"]:
            output_name = os.path.join(kw['output_folder'],
                self.path("rss", None, lang))
            deps = []
            posts = [x for x in self.timeline if x.use_in_feeds][:10]
            for post in posts:
                deps += post.deps(lang)
            yield {
                'basename': 'render_rss',
                'name': output_name,
                'file_dep': deps,
                'targets': [output_name],
                'actions': [(utils.generic_rss_renderer,
                    (lang, kw["blog_title"], kw["blog_url"],
                    kw["blog_description"], posts, output_name))],
                'clean': True,
                'uptodate': [config_changed(kw)],
            }

    def gen_task_render_listings(self, **kw):
        """
        Required keyword arguments:

        listings_folder
        output_folder
        default_lang
        """

        def render_listing(in_name, out_name):
            with open(in_name, 'r') as fd:
                try:
                    lexer = get_lexer_for_filename(in_name)
                except:
                    lexer = TextLexer()
                code = highlight(fd.read(), lexer,
                    HtmlFormatter(cssclass='code',
                        linenos="table",
                        nowrap=False,
                        lineanchors=utils.slugify(f),
                        anchorlinenos=True))
            title = os.path.basename(in_name)
            crumbs = out_name.split(os.sep)[1:-1] + [title]
            # TODO: write this in human
            paths = ['/'.join(['..'] * (len(crumbs) - 2 - i)) for i in range(len(crumbs[:-2]))] + ['.', '#']
            context = {
                'code': code,
                'title': title,
                'crumbs': zip(paths, crumbs),
                'lang': kw['default_lang'],
                'description': title,
                }
            self.render_template('listing.tmpl', out_name, context)
        flag = True
        template_deps = self.template_deps('listing.tmpl')
        for root, dirs, files in os.walk(kw['listings_folder']):
            # Render all files
            for f in files:
                flag = False
                in_name = os.path.join(root, f)
                out_name = os.path.join(
                    kw['output_folder'],
                    root,
                    f) + '.html'
                yield {
                    'basename': 'render_listings',
                    'name': out_name.encode('utf8'),
                    'file_dep': template_deps + [in_name],
                    'targets': [out_name],
                    'actions': [(render_listing, [in_name, out_name])],
                }
        if flag:
            yield {
                'basename': 'render_listings',
                'actions': [],
            }

    def gen_task_render_galleries(self, **kw):
        """Render image galleries.

        Required keyword arguments:

        image_size
        thumbnail_size,
        default_lang,
        output_folder,
        use_filename_as_title
        """

        # FIXME: lots of work is done even when images don't change,
        # which should be moved into the task.
        # Also, this is getting complex enough to be refactored into a file.

        template_name = "gallery.tmpl"

        gallery_list = glob.glob("galleries/*")
        # Fail quick if we don't have galleries, so we don't
        # require PIL
        Image = None
        if not gallery_list:
            yield {
                'basename': 'render_galleries',
                'actions': [],
                }
            return
        try:
            import Image as _Image
            import ExifTags
            Image = _Image
        except ImportError:
            try:
                from PIL import Image as _Image, ExifTags
                Image = _Image
            except ImportError:
                pass
        if Image:
            def _resize_image(src, dst, max_size):
                im = Image.open(src)
                w, h = im.size
                if w > max_size or h > max_size:
                    size = max_size, max_size
                    try:
                        exif = im._getexif()
                    except AttributeError:
                        exif = None
                    if exif is not None:
                        for tag, value in exif.items():
                            decoded = ExifTags.TAGS.get(tag, tag)

                            if decoded == 'Orientation':
                                if value == 3:
                                    im = im.rotate(180)
                                elif value == 6:
                                    im = im.rotate(270)
                                elif value == 8:
                                    im = im.rotate(90)

                                break

                    im.thumbnail(size, Image.ANTIALIAS)
                    im.save(dst)

                else:
                    utils.copy_file(src, dst)

            def create_thumb(src, dst):
                return _resize_image(src, dst, kw['thumbnail_size'])

            def create_resized_image(src, dst):
                return _resize_image(src, dst, kw['max_image_size'])

            dates = {}
            def image_date(src):
                #import doit.tools; doit.tools.set_trace()
                if src not in dates:
                    im = Image.open(src)
                    try:
                        exif = im._getexif()
                    except AttributeError:
                        exif = None
                    if exif is not None:
                        for tag, value in exif.items():
                            decoded = ExifTags.TAGS.get(tag, tag)
                            if decoded == 'DateTimeOriginal':
                                dates[src] = datetime.datetime.strptime(value, r'%Y:%m:%d %H:%M:%S')
                                break
                if src not in dates:
                    dates[src] = datetime.datetime.fromtimestamp(os.stat(src).st_mtime)
                return dates[src]

        else:
            create_thumb = utils.copy_file
            create_resized_image = utils.copy_file

        # gallery_path is "gallery/name"
        for gallery_path in gallery_list:
            # gallery_name is "name"
            gallery_name = os.path.basename(gallery_path)
            # output_gallery is "output/GALLERY_PATH/name"
            output_gallery = os.path.dirname(os.path.join(kw["output_folder"],
                self.path("gallery", gallery_name, None)))
            if not os.path.isdir(output_gallery):
                yield {
                    'basename': 'render_galleries',
                    'name': output_gallery,
                    'actions': [(os.makedirs, (output_gallery,))],
                    'targets': [output_gallery],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                    }
            # image_list contains "gallery/name/image_name.jpg"
            image_list = glob.glob(gallery_path + "/*jpg") +\
                glob.glob(gallery_path + "/*JPG") +\
                glob.glob(gallery_path + "/*PNG") +\
                glob.glob(gallery_path + "/*png")

            # Filter ignore images
            try:
                def add_gallery_path(index):
                    return "{0}/{1}".format(gallery_path, index)

                exclude_path = os.path.join(gallery_path, "exclude.meta")
                try:
                    f = open(exclude_path, 'r')
                    excluded_image_name_list = f.read().split()
                except IOError:
                    excluded_image_name_list = []

                excluded_image_list = map(add_gallery_path,
                    excluded_image_name_list)
                image_set = set(image_list) - set(excluded_image_list)
                image_list = list(image_set)
            except IOError:
                pass

            image_list = [x for x in image_list if "thumbnail" not in x]
            # Sort by date
            image_list.sort(cmp=lambda a,b: cmp(image_date(a), image_date(b)))
            image_name_list = [os.path.basename(x) for x in image_list]

            thumbs = []
            # Do thumbnails and copy originals
            for img, img_name in zip(image_list, image_name_list):
                # img is "galleries/name/image_name.jpg"
                # img_name is "image_name.jpg"
                # fname, ext are "image_name", ".jpg"
                fname, ext = os.path.splitext(img_name)
                # thumb_path is
                # "output/GALLERY_PATH/name/image_name.thumbnail.jpg"
                thumb_path = os.path.join(output_gallery,
                    fname + ".thumbnail" + ext)
                # thumb_path is "output/GALLERY_PATH/name/image_name.jpg"
                orig_dest_path = os.path.join(output_gallery, img_name)
                thumbs.append(os.path.basename(thumb_path))
                yield {
                    'basename': 'render_galleries',
                    'name': thumb_path,
                    'file_dep': [img],
                    'targets': [thumb_path],
                    'actions': [
                        (create_thumb, (img, thumb_path))
                    ],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                }
                yield {
                    'basename': 'render_galleries',
                    'name': orig_dest_path,
                    'file_dep': [img],
                    'targets': [orig_dest_path],
                    'actions': [
                        (create_resized_image, (img, orig_dest_path))
                    ],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                }

            # Remove excluded images
            if excluded_image_name_list:
                for img, img_name in zip(excluded_image_list,
                        excluded_image_name_list):
                    # img_name is "image_name.jpg"
                    # fname, ext are "image_name", ".jpg"
                    #import pdb
                    #pdb.set_trace()
                    fname, ext = os.path.splitext(img_name)
                    excluded_thumb_dest_path = os.path.join(output_gallery,
                        fname + ".thumbnail" + ext)
                    excluded_dest_path = os.path.join(output_gallery, img_name)
                    yield {
                        'basename': 'render_galleries',
                        'name': excluded_thumb_dest_path,
                        'file_dep': [exclude_path],
                        #'targets': [excluded_thumb_dest_path],
                        'actions': [
                            (utils.remove_file, (excluded_thumb_dest_path,))
                        ],
                        'clean': True,
                        'uptodate': [config_changed(kw)],
                    }
                    yield {
                        'basename': 'render_galleries',
                        'name': excluded_dest_path,
                        'file_dep': [exclude_path],
                        #'targets': [excluded_dest_path],
                        'actions': [
                            (utils.remove_file, (excluded_dest_path,))
                        ],
                        'clean': True,
                        'uptodate': [config_changed(kw)],
                    }

            output_name = os.path.join(output_gallery, "index.html")
            context = {}
            context["lang"] = kw["default_lang"]
            context["title"] = os.path.basename(gallery_path)
            context["description"] = kw["blog_description"]
            if kw['use_filename_as_title']:
                img_titles = ['title="%s"' % utils.unslugify(fn[:-4])
                              for fn in image_name_list]
            else:
                img_titles = [''] * len(image_name_list)
            context["images"] = zip(image_name_list, thumbs, img_titles)
            context["permalink"] = self.link("gallery", gallery_name, None)

            # Use galleries/name/index.txt to generate a blurb for
            # the gallery, if it exists
            index_path = os.path.join(gallery_path, "index.txt")
            index_dst_path = os.path.join(gallery_path, "index.html")
            if os.path.exists(index_path):
                compile_html = self.get_compile_html(index_path)
                yield {
                    'basename': 'render_galleries',
                    'name': index_dst_path.encode('utf-8'),
                    'file_dep': [index_path],
                    'targets': [index_dst_path],
                    'actions': [(compile_html,
                        [index_path, index_dst_path])],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                }

            file_dep = self.template_deps(template_name) + image_list

            def render_gallery(output_name, context, index_dst_path):
                if os.path.exists(index_dst_path):
                    with codecs.open(index_dst_path, "rb", "utf8") as fd:
                        context['text'] = fd.read()
                    file_dep.append(index_dst_path)
                else:
                    context['text'] = ''
                self.render_template(template_name, output_name, context)

            yield {
                'basename': 'render_galleries',
                'name': gallery_path,
                'file_dep': file_dep,
                'targets': [output_name],
                'actions': [(render_gallery,
                    (output_name, context, index_dst_path))],
                'clean': True,
                'uptodate': [config_changed(kw)],
            }

    @staticmethod
    def gen_task_redirect(**kw):
        """Generate redirections.

        Required keyword arguments:

        redirections
        output_folder
        """

        def create_redirect(src, dst):
            with codecs.open(src, "wb+", "utf8") as fd:
                fd.write(('<head>' +
                '<meta HTTP-EQUIV="REFRESH" content="0; url=%s">' +
                '</head>') % dst)

        if not kw['redirections']:
            # If there are no redirections, still needs to create a
            # dummy action so dependencies don't fail
            yield {
                'basename': 'redirect',
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }
        else:
            for src, dst in kw["redirections"]:
                src_path = os.path.join(kw["output_folder"], src)
                yield {
                    'basename': 'redirect',
                    'name': src_path,
                    'targets': [src_path],
                    'actions': [(create_redirect, (src_path, dst))],
                    'clean': True,
                    'uptodate': [config_changed(kw)],
                    }

    @staticmethod
    def gen_task_copy_files(**kw):
        """Copy static files into the output folder.

        required keyword arguments:

        output_folder
        files_folders
        """

        flag = False
        for src in kw['files_folders']:
            dst = kw['output_folder']
            filters = kw['filters']
            real_dst = os.path.join(dst, kw['files_folders'][src])
            for task in utils.copy_tree(src, real_dst, link_cutoff=dst):
                flag = True
                task['basename'] = 'copy_files'
                task['uptodate'] = task.get('uptodate', []) +\
                    [config_changed(kw)]
                yield utils.apply_filters(task, filters)
        if not flag:
            yield {
                'basename': 'copy_files',
                'actions': (),
            }

    @staticmethod
    def gen_task_copy_assets(**kw):
        """Create tasks to copy the assets of the whole theme chain.

        If a file is present on two themes, use the version
        from the "youngest" theme.

        Required keyword arguments:

        themes
        output_folder

        """
        tasks = {}
        for theme_name in kw['themes']:
            src = os.path.join(utils.get_theme_path(theme_name), 'assets')
            dst = os.path.join(kw['output_folder'], 'assets')
            for task in utils.copy_tree(src, dst):
                if task['name'] in tasks:
                    continue
                tasks[task['name']] = task
                task['uptodate'] = task.get('uptodate', []) + \
                    [config_changed(kw)]
                task['basename'] = 'copy_assets'
                yield utils.apply_filters(task, kw['filters'])

    @staticmethod
    def gen_task_build_bundles(**kw):
        """Create tasks to build bundles from theme assets.

        theme_bundles
        output_folder
        filters
        """

        def build_bundle(output, inputs):
            env = webassets.Environment(
                os.path.join(kw['output_folder'], os.path.dirname(output)),
                os.path.dirname(output))
            bundle = webassets.Bundle(*inputs,
                output=os.path.basename(output))
            env.register(output, bundle)
            # This generates the file
            env[output].urls()

        for name, files in kw['theme_bundles'].items():
            output_path = os.path.join(kw['output_folder'], name)
            dname = os.path.dirname(name)
            file_dep = [os.path.join('output', dname, fname)
                for fname in files]
            task = {
                'task_dep': ['copy_assets', 'copy_files'],
                'file_dep': file_dep,
                'name': name,
                'actions': [(build_bundle, (name, files))],
                'targets': [os.path.join(kw['output_folder'], name)],
                'basename': 'build_bundles',
                'uptodate': [config_changed(kw)]
                }
            yield utils.apply_filters(task, kw['filters'])


    @staticmethod
    def new_post(post_pages, is_post=True):
        # Guess where we should put this
        for path, _, _, use_in_rss in post_pages:
            if use_in_rss == is_post:
                break
        else:
            path = post_pages[0][0]

        print "Creating New Post"
        print "-----------------\n"
        title = raw_input("Enter title: ").decode(sys.stdin.encoding)
        slug = utils.slugify(title)
        data = u'\n'.join([
            title,
            slug,
            datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            ])
        output_path = os.path.dirname(path)
        meta_path = os.path.join(output_path, slug + ".meta")
        pattern = os.path.basename(path)
        if pattern.startswith("*."):
            suffix = pattern[1:]
        else:
            suffix = ".txt"
        txt_path = os.path.join(output_path, slug + suffix)

        if os.path.isfile(meta_path) or os.path.isfile(txt_path):
            print "The title already exists!"
            exit()

        with codecs.open(meta_path, "wb+", "utf8") as fd:
            fd.write(data)
        with codecs.open(txt_path, "wb+", "utf8") as fd:
            fd.write(u"Write your post here.")
        print "Your post's metadata is at: ", meta_path
        print "Your post's text is at: ", txt_path

    @classmethod
    def new_page(cls):
        cls.new_post(False)

    @classmethod
    def gen_task_new_post(cls, post_pages):
        """Create a new post (interactive)."""
        yield {
            "basename": "new_post",
            "actions": [PythonInteractiveAction(cls.new_post, (post_pages,))],
            }

    @classmethod
    def gen_task_new_page(cls, post_pages):
        """Create a new post (interactive)."""
        yield {
            "basename": "new_page",
            "actions": [PythonInteractiveAction(cls.new_post,
                (post_pages, False,))],
            }

    @staticmethod
    def gen_task_deploy(**kw):
        """Deploy site.

        Required keyword arguments:

        commands

        """
        yield {
            "basename": "deploy",
            "actions": kw['commands'],
            "verbosity": 2,
            }

    @staticmethod
    def gen_task_sitemap(**kw):
        """Generate Google sitemap.

        Required keyword arguments:

        blog_url
        output_folder
        """

        output_path = os.path.abspath(kw['output_folder'])
        sitemap_path = os.path.join(output_path, "sitemap.xml.gz")

        def sitemap():
            # Generate config
            config_data = """<?xml version="1.0" encoding="UTF-8"?>
    <site
    base_url="%s"
    store_into="%s"
    verbose="1" >
    <directory path="%s" url="%s" />
    <filter action="drop" type="wildcard" pattern="*~" />
    <filter action="drop" type="regexp" pattern="/\.[^/]*" />
    </site>""" % (
                kw["blog_url"],
                sitemap_path,
                output_path,
                kw["blog_url"],
            )
            config_file = tempfile.NamedTemporaryFile(delete=False)
            config_file.write(config_data)
            config_file.close()

            # Generate sitemap
            import sitemap_gen as smap
            sitemap = smap.CreateSitemapFromFile(config_file.name, True)
            if not sitemap:
                smap.output.Log('Configuration file errors -- exiting.', 0)
            else:
                sitemap.Generate()
                smap.output.Log('Number of errors: %d' %
                    smap.output.num_errors, 1)
                smap.output.Log('Number of warnings: %d' %
                    smap.output.num_warns, 1)
            os.unlink(config_file.name)

        yield {
            "basename": "sitemap",
            "task_dep": [
                "render_archive",
                "render_indexes",
                "render_pages",
                "render_posts",
                "render_rss",
                "render_sources",
                "render_tags"],
            "targets": [sitemap_path],
            "actions": [(sitemap,)],
            "uptodate": [config_changed(kw)],
            "clean": True,
        }

    @staticmethod
    def task_serve(**kw):
        """
        Start test server. (doit serve [--address 127.0.0.1] [--port 8000])
        By default, the server runs on port 8000 on the IP address 127.0.0.1.

        required keyword arguments:

        output_folder
        """

        def serve(address, port):
            from BaseHTTPServer import HTTPServer
            from SimpleHTTPServer import SimpleHTTPRequestHandler

            class OurHTTPRequestHandler(SimpleHTTPRequestHandler):
                extensions_map = dict(SimpleHTTPRequestHandler.extensions_map)
                extensions_map[""] = "text/plain"

            os.chdir(kw['output_folder'])

            httpd = HTTPServer((address, port), OurHTTPRequestHandler)
            sa = httpd.socket.getsockname()
            print "Serving HTTP on", sa[0], "port", sa[1], "..."
            httpd.serve_forever()

        yield {
            "basename": 'serve',
            "actions": [(serve,)],
            "verbosity": 2,
            "params": [{'short': 'a',
                        'name': 'address',
                        'long': 'address',
                        'type': str,
                        'default': '127.0.0.1',
                        'help': 'Bind address (default: 127.0.0.1)'},
                       {'short': 'p',
                        'name': 'port',
                        'long': 'port',
                        'type': int,
                        'default': 8000,
                        'help': 'Port number (default: 8000)'}],
            }

    @staticmethod
    def task_install_theme():
        """Install theme. (doit install_theme -n themename [-u URL]|[-l])."""

        def install_theme(name, url, listing):
            if name is None and not listing:
                print "This command needs either the -n or the -l option."
                return False
            data = urllib2.urlopen(url).read()
            data = json.loads(data)
            if listing:
                print "Themes:"
                print "-------"
                for theme in sorted(data.keys()):
                    print theme
                return True
            else:
                if name in data:
                    if os.path.isfile("themes"):
                        raise IOError("'themes' isn't a directory!")
                    elif not os.path.isdir("themes"):
                        try:
                            os.makedirs("themes")
                        except:
                            raise OSError("mkdir 'theme' error!")
                    print 'Downloading: %s' % data[name]
                    zip_file = StringIO()
                    zip_file.write(urllib2.urlopen(data[name]).read())
                    print 'Extracting: %s into themes' % name
                    utils.extract_all(zip_file)
                else:
                    print "Can't find theme %s" % name
                    return False

        yield {
            "basename": 'install_theme',
            "actions": [(install_theme,)],
            "verbosity": 2,
            "params": [
                {
                    'short': 'u',
                    'name': 'url',
                    'long': 'url',
                    'type': str,
                    'default': 'http://nikola.ralsina.com.ar/themes/index.json',
                    'help': 'URL for theme collection.'
                },
                {
                    'short': 'l',
                    'name': 'listing',
                    'long': 'list',
                    'type': bool,
                    'default': False,
                    'help': 'List available themes.'
                },
                {
                    'short': 'n',
                    'name': 'name',
                    'long': 'name',
                    'type': str,
                    'default': None,
                    'help': 'Name of theme to install.'
                }],
            }

    @staticmethod
    def task_bootswatch_theme():
        """Given a swatch name and a parent theme, creates a custom theme."""
        def bootswatch_theme(name, parent, swatch):
            print "Creating %s theme from %s and %s" % (name, swatch, parent)
            try:
                os.makedirs(os.path.join('themes', name, 'assets', 'css'))
            except:
                pass
            for fname in ('bootstrap.min.css', 'bootstrap.css'):
                url = 'http://bootswatch.com/%s/%s' % (swatch, fname)
                print "Downloading: ", url
                data = urllib2.urlopen(url).read()
                with open(os.path.join(
                    'themes', name, 'assets', 'css', fname), 'wb+') as output:
                    output.write(data)

            with open(os.path.join('themes', name, 'parent'), 'wb+') as output:
                output.write(parent)
            print 'Theme created. Change the THEME setting to "%s" to use it.'\
                % name

        yield {
            "basename": 'bootswatch_theme',
            "actions": [(bootswatch_theme,)],
            "verbosity": 2,
            "params": [
                {
                    'short': 'p',
                    'name': 'parent',
                    'long': 'parent',
                    'type': str,
                    'default': 'site',
                    'help': 'Name of parent theme.'
                },
                {
                    'short': 's',
                    'name': 'swatch',
                    'long': 'swatch',
                    'type': str,
                    'default': 'slate',
                    'help': 'Name of the swatch from bootswatch.com'
                },
                {
                    'short': 'n',
                    'name': 'name',
                    'long': 'name',
                    'type': str,
                    'default': 'custom',
                    'help': 'Name of the new theme'
                }
                ],
        }


def nikola_main():
    print "Starting doit..."
    os.system("doit -f %s" % __file__)
