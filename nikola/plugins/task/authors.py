# -*- coding: utf-8 -*-

# Copyright © 2015-2016 Juanjo Conti and others.

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

"""Render the author pages and feeds."""

from __future__ import unicode_literals
import os
import natsort
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA
from collections import defaultdict

from blinker import signal

from nikola.plugin_categories import Task
from nikola import utils


class RenderAuthors(Task):
    """Render the author pages and feeds."""

    name = "render_authors"
    posts_per_author = None

    def set_site(self, site):
        """Set Nikola site."""
        self.generate_author_pages = False
        if site.config["ENABLE_AUTHOR_PAGES"]:
            site.register_path_handler('author_index', self.author_index_path)
            site.register_path_handler('author', self.author_path)
            site.register_path_handler('author_atom', self.author_atom_path)
            site.register_path_handler('author_rss', self.author_rss_path)
            signal('scanned').connect(self.posts_scanned)
        return super(RenderAuthors, self).set_site(site)

    def posts_scanned(self, event):
        """Called after posts are scanned via signal."""
        self.generate_author_pages = self.site.config["ENABLE_AUTHOR_PAGES"] and len(self._posts_per_author()) > 1
        self.site.GLOBAL_CONTEXT["author_pages_generated"] = self.generate_author_pages

    def gen_tasks(self):
        """Render the author pages and feeds."""
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "blog_title": self.site.config["BLOG_TITLE"],
            "site_url": self.site.config["SITE_URL"],
            "base_url": self.site.config["BASE_URL"],
            "messages": self.site.MESSAGES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            'author_path': self.site.config['AUTHOR_PATH'],
            "author_pages_are_indexes": self.site.config['AUTHOR_PAGES_ARE_INDEXES'],
            "generate_rss": self.site.config['GENERATE_RSS'],
            "feed_teasers": self.site.config["FEED_TEASERS"],
            "feed_plain": self.site.config["FEED_PLAIN"],
            "feed_link_append_query": self.site.config["FEED_LINKS_APPEND_QUERY"],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "feed_length": self.site.config['FEED_LENGTH'],
            "tzinfo": self.site.tzinfo,
            "pretty_urls": self.site.config['PRETTY_URLS'],
            "strip_indexes": self.site.config['STRIP_INDEXES'],
            "index_file": self.site.config['INDEX_FILE'],
        }

        self.site.scan_posts()
        yield self.group_task()

        if self.generate_author_pages:
            yield self.list_authors_page(kw)

            if not self._posts_per_author():  # this may be self.site.posts_per_author
                return

            author_list = list(self._posts_per_author().items())

            def render_lists(author, posts):
                """Render author pages as RSS files and lists/indexes."""
                post_list = sorted(posts, key=lambda a: a.date)
                post_list.reverse()
                for lang in kw["translations"]:
                    if kw["show_untranslated_posts"]:
                        filtered_posts = post_list
                    else:
                        filtered_posts = [x for x in post_list if x.is_translation_available(lang)]
                    if kw["generate_rss"]:
                        yield self.author_rss(author, lang, filtered_posts, kw)
                    # Render HTML
                    if kw['author_pages_are_indexes']:
                        yield self.author_page_as_index(author, lang, filtered_posts, kw)
                    else:
                        yield self.author_page_as_list(author, lang, filtered_posts, kw)

            for author, posts in author_list:
                for task in render_lists(author, posts):
                    yield task

    def _create_authors_page(self, kw):
        """Create a global "all authors" page for each language."""
        template_name = "authors.tmpl"
        kw = kw.copy()
        for lang in kw["translations"]:
            authors = natsort.natsorted([author for author in self._posts_per_author().keys()],
                                        alg=natsort.ns.F | natsort.ns.IC)
            has_authors = (authors != [])
            kw['authors'] = authors
            output_name = os.path.join(
                kw['output_folder'], self.site.path('author_index', None, lang))
            context = {}
            if has_authors:
                context["title"] = kw["messages"][lang]["Authors"]
                context["items"] = [(author, self.site.link("author", author, lang)) for author
                                    in authors]
                context["description"] = context["title"]
            else:
                context["items"] = None
            context["permalink"] = self.site.link("author_index", None, lang)
            context["pagekind"] = ["list", "authors_page"]
            task = self.site.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            )
            task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.authors:page')]
            task['basename'] = str(self.name)
            yield task

    def list_authors_page(self, kw):
        """Create a global "all authors" page for each language."""
        yield self._create_authors_page(kw)

    def _get_title(self, author):
        return author

    def _get_description(self, author, lang):
        descriptions = self.site.config['AUTHOR_PAGES_DESCRIPTIONS']
        return descriptions[lang][author] if lang in descriptions and author in descriptions[lang] else None

    def author_page_as_index(self, author, lang, post_list, kw):
        """Render a sort of index page collection using only this author's posts."""
        kind = "author"

        def page_link(i, displayed_i, num_pages, force_addition, extension=None):
            feed = "_atom" if extension == ".atom" else ""
            return utils.adjust_name_for_index_link(self.site.link(kind + feed, author, lang), i, displayed_i, lang, self.site, force_addition, extension)

        def page_path(i, displayed_i, num_pages, force_addition, extension=None):
            feed = "_atom" if extension == ".atom" else ""
            return utils.adjust_name_for_index_path(self.site.path(kind + feed, author, lang), i, displayed_i, lang, self.site, force_addition, extension)

        context_source = {}
        title = self._get_title(author)
        if kw["generate_rss"]:
            # On a author page, the feeds include the author's feeds
            rss_link = ("""<link rel="alternate" type="application/rss+xml" """
                        """title="RSS for author """
                        """{0} ({1})" href="{2}">""".format(
                            title, lang, self.site.link(kind + "_rss", author, lang)))
            context_source['rss_link'] = rss_link
        context_source["author"] = title
        indexes_title = kw["messages"][lang]["Posts by %s"] % title
        context_source["description"] = self._get_description(author, lang)
        context_source["pagekind"] = ["index", "author_page"]
        template_name = "authorindex.tmpl"

        yield self.site.generic_index_renderer(lang, post_list, indexes_title, template_name, context_source, kw, str(self.name), page_link, page_path)

    def author_page_as_list(self, author, lang, post_list, kw):
        """Render a single flat link list with this author's posts."""
        kind = "author"
        template_name = "author.tmpl"
        output_name = os.path.join(kw['output_folder'], self.site.path(
            kind, author, lang))
        context = {}
        context["lang"] = lang
        title = self._get_title(author)
        context["author"] = title
        context["title"] = kw["messages"][lang]["Posts by %s"] % title
        context["posts"] = post_list
        context["permalink"] = self.site.link(kind, author, lang)
        context["kind"] = kind
        context["description"] = self._get_description(author, lang)
        context["pagekind"] = ["list", "author_page"]
        task = self.site.generic_post_list_renderer(
            lang,
            post_list,
            output_name,
            template_name,
            kw['filters'],
            context,
        )
        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.authors:list')]
        task['basename'] = str(self.name)
        yield task

    def author_rss(self, author, lang, posts, kw):
        """Create a RSS feed for a single author in a given language."""
        kind = "author"
        # Render RSS
        output_name = os.path.normpath(
            os.path.join(kw['output_folder'],
                         self.site.path(kind + "_rss", author, lang)))
        feed_url = urljoin(self.site.config['BASE_URL'], self.site.link(kind + "_rss", author, lang).lstrip('/'))
        deps = []
        deps_uptodate = []
        post_list = sorted(posts, key=lambda a: a.date)
        post_list.reverse()
        for post in post_list:
            deps += post.deps(lang)
            deps_uptodate += post.deps_uptodate(lang)
        task = {
            'basename': str(self.name),
            'name': output_name,
            'file_dep': deps,
            'targets': [output_name],
            'actions': [(utils.generic_rss_renderer,
                        (lang, "{0} ({1})".format(kw["blog_title"](lang), self._get_title(author)),
                         kw["site_url"], None, post_list,
                         output_name, kw["feed_teasers"], kw["feed_plain"], kw['feed_length'],
                         feed_url, None, kw["feed_link_append_query"]))],
            'clean': True,
            'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.authors:rss')] + deps_uptodate,
            'task_dep': ['render_posts'],
        }
        return utils.apply_filters(task, kw['filters'])

    def slugify_author_name(self, name, lang=None):
        """Slugify an author name."""
        if lang is None:  # TODO: remove in v8
            utils.LOGGER.warn("RenderAuthors.slugify_author_name() called without language!")
            lang = ''
        if self.site.config['SLUG_AUTHOR_PATH']:
            name = utils.slugify(name, lang)
        return name

    def author_index_path(self, name, lang):
        """Link to the author's index.

        Example:

        link://authors/ => /authors/index.html
        """
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['AUTHOR_PATH'],
                              self.site.config['INDEX_FILE']] if _f]

    def author_path(self, name, lang):
        """Link to an author's page.

        Example:

        link://author/joe => /authors/joe.html
        """
        if self.site.config['PRETTY_URLS']:
            return [_f for _f in [
                self.site.config['TRANSLATIONS'][lang],
                self.site.config['AUTHOR_PATH'],
                self.slugify_author_name(name, lang),
                self.site.config['INDEX_FILE']] if _f]
        else:
            return [_f for _f in [
                self.site.config['TRANSLATIONS'][lang],
                self.site.config['AUTHOR_PATH'],
                self.slugify_author_name(name, lang) + ".html"] if _f]

    def author_atom_path(self, name, lang):
        """Link to an author's Atom feed.

        Example:

        link://author_atom/joe => /authors/joe.atom
        """
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['AUTHOR_PATH'], self.slugify_author_name(name, lang) + ".atom"] if
                _f]

    def author_rss_path(self, name, lang):
        """Link to an author's RSS feed.

        Example:

        link://author_rss/joe => /authors/joe.rss
        """
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['AUTHOR_PATH'], self.slugify_author_name(name, lang) + ".xml"] if
                _f]

    def _add_extension(self, path, extension):
        path[-1] += extension
        return path

    def _posts_per_author(self):
        """Return a dict of posts per author."""
        if self.posts_per_author is None:
            self.posts_per_author = defaultdict(list)
            for post in self.site.timeline:
                if post.is_post:
                    self.posts_per_author[post.author()].append(post)
        return self.posts_per_author
