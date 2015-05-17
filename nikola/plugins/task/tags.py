# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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

from __future__ import unicode_literals
import json
import os
import sys
import natsort
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA

from nikola.plugin_categories import Task
from nikola import utils


class RenderTags(Task):
    """Render the tag/category pages and feeds."""

    name = "render_tags"

    def set_site(self, site):
        site.register_path_handler('tag_index', self.tag_index_path)
        site.register_path_handler('category_index', self.category_index_path)
        site.register_path_handler('tag', self.tag_path)
        site.register_path_handler('tag_atom', self.tag_atom_path)
        site.register_path_handler('tag_rss', self.tag_rss_path)
        site.register_path_handler('category', self.category_path)
        site.register_path_handler('category_atom', self.category_atom_path)
        site.register_path_handler('category_rss', self.category_rss_path)
        return super(RenderTags, self).set_site(site)

    def gen_tasks(self):
        """Render the tag pages and feeds."""

        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "blog_title": self.site.config["BLOG_TITLE"],
            "site_url": self.site.config["SITE_URL"],
            "base_url": self.site.config["BASE_URL"],
            "messages": self.site.MESSAGES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            'tag_path': self.site.config['TAG_PATH'],
            "tag_pages_are_indexes": self.site.config['TAG_PAGES_ARE_INDEXES'],
            "tag_pages_descriptions": self.site.config['TAG_PAGES_DESCRIPTIONS'],
            'category_path': self.site.config['CATEGORY_PATH'],
            'category_prefix': self.site.config['CATEGORY_PREFIX'],
            "category_pages_are_indexes": self.site.config['CATEGORY_PAGES_ARE_INDEXES'],
            "category_pages_descriptions": self.site.config['CATEGORY_PAGES_DESCRIPTIONS'],
            "generate_rss": self.site.config['GENERATE_RSS'],
            "rss_teasers": self.site.config["RSS_TEASERS"],
            "rss_plain": self.site.config["RSS_PLAIN"],
            "rss_link_append_query": self.site.config["RSS_LINKS_APPEND_QUERY"],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "feed_length": self.site.config['FEED_LENGTH'],
            "taglist_minimum_post_count": self.site.config['TAGLIST_MINIMUM_POSTS'],
            "tzinfo": self.site.tzinfo,
            "pretty_urls": self.site.config['PRETTY_URLS'],
            "strip_indexes": self.site.config['STRIP_INDEXES'],
            "index_file": self.site.config['INDEX_FILE'],
        }

        self.site.scan_posts()
        yield self.group_task()

        yield self.list_tags_page(kw)

        if not self.site.posts_per_tag and not self.site.posts_per_category:
            return

        if kw['category_path'] == kw['tag_path']:
            tags = {self.slugify_tag_name(tag): tag for tag in self.site.posts_per_tag.keys()}
            cats = {tuple(self.slugify_category_name(category)): category for category in self.site.posts_per_category.keys()}
            categories = {k[0]: v for k, v in cats.items() if len(k) == 1}
            intersect = set(tags.keys()) & set(categories.keys())
            if len(intersect) > 0:
                for slug in intersect:
                    utils.LOGGER.error("Category '{0}' and tag '{1}' both have the same slug '{2}'!".format('/'.join(categories[slug]), tags[slug], slug))
                sys.exit(1)

        # Test for category slug clashes
        categories = {}
        for category in self.site.posts_per_category.keys():
            slug = tuple(self.slugify_category_name(category))
            for part in slug:
                if len(part) == 0:
                    utils.LOGGER.error("Category '{0}' yields invalid slug '{1}'!".format(category, '/'.join(slug)))
                    sys.exit(1)
            if slug in categories:
                other_category = categories[slug]
                utils.LOGGER.error('You have categories that are too similar: {0} and {1}'.format(category, other_category))
                utils.LOGGER.error('Category {0} is used in: {1}'.format(category, ', '.join([p.source_path for p in self.site.posts_per_category[category]])))
                utils.LOGGER.error('Category {0} is used in: {1}'.format(other_category, ', '.join([p.source_path for p in self.site.posts_per_category[other_category]])))
                sys.exit(1)
            categories[slug] = category

        tag_list = list(self.site.posts_per_tag.items())
        cat_list = list(self.site.posts_per_category.items())

        def render_lists(tag, posts, is_category=True):
            post_list = sorted(posts, key=lambda a: a.date)
            post_list.reverse()
            for lang in kw["translations"]:
                if kw["show_untranslated_posts"]:
                    filtered_posts = post_list
                else:
                    filtered_posts = [x for x in post_list if x.is_translation_available(lang)]
                if kw["generate_rss"]:
                    yield self.tag_rss(tag, lang, filtered_posts, kw, is_category)
                # Render HTML
                if kw['category_pages_are_indexes'] if is_category else kw['tag_pages_are_indexes']:
                    yield self.tag_page_as_index(tag, lang, filtered_posts, kw, is_category)
                else:
                    yield self.tag_page_as_list(tag, lang, filtered_posts, kw, is_category)

        for tag, posts in tag_list:
            for task in render_lists(tag, posts, False):
                yield task

        for path, posts in cat_list:
            for task in render_lists(path, posts, True):
                yield task

        # Tag cloud json file
        tag_cloud_data = {}
        for tag, posts in self.site.posts_per_tag.items():
            if tag in self.site.config['HIDDEN_TAGS']:
                continue
            tag_posts = dict(posts=[{'title': post.meta[post.default_lang]['title'],
                                     'date': post.date.strftime('%m/%d/%Y'),
                                     'isodate': post.date.isoformat(),
                                     'url': post.permalink(post.default_lang)}
                                    for post in reversed(sorted(self.site.timeline, key=lambda post: post.date))
                                    if tag in post.alltags])
            tag_cloud_data[tag] = [len(posts), self.site.link(
                'tag', tag, self.site.config['DEFAULT_LANG']), tag_posts]
        output_name = os.path.join(kw['output_folder'],
                                   'assets', 'js', 'tag_cloud_data.json')

        def write_tag_data(data):
            utils.makedirs(os.path.dirname(output_name))
            with open(output_name, 'w+') as fd:
                json.dump(data, fd)

        if self.site.config['WRITE_TAG_CLOUD']:
            task = {
                'basename': str(self.name),
                'name': str(output_name)
            }

            task['uptodate'] = [utils.config_changed(tag_cloud_data, 'nikola.plugins.task.tags:tagdata')]
            task['targets'] = [output_name]
            task['actions'] = [(write_tag_data, [tag_cloud_data])]
            task['clean'] = True
            yield utils.apply_filters(task, kw['filters'])

    def _create_tags_page(self, kw, include_tags=True, include_categories=True):
        """a global "all your tags/categories" page for each language"""
        tags = natsort.natsorted([tag for tag in self.site.posts_per_tag.keys()
                                  if len(self.site.posts_per_tag[tag]) >= kw["taglist_minimum_post_count"]],
                                 alg=natsort.ns.F | natsort.ns.IC)
        categories = [cat.category_name for cat in self.site.category_hierarchy]
        has_tags = (tags != []) and include_tags
        has_categories = (categories != []) and include_categories
        template_name = "tags.tmpl"
        kw = kw.copy()
        if include_tags:
            kw['tags'] = tags
        if include_categories:
            kw['categories'] = categories
        for lang in kw["translations"]:
            output_name = os.path.join(
                kw['output_folder'], self.site.path('tag_index' if has_tags else 'category_index', None, lang))
            output_name = output_name
            context = {}
            if has_categories and has_tags:
                context["title"] = kw["messages"][lang]["Tags and Categories"]
            elif has_categories:
                context["title"] = kw["messages"][lang]["Categories"]
            else:
                context["title"] = kw["messages"][lang]["Tags"]
            if has_tags:
                context["items"] = [(tag, self.site.link("tag", tag, lang)) for tag
                                    in tags]
            else:
                context["items"] = None
            if has_categories:
                context["cat_items"] = [(tag, self.site.link("category", tag, lang)) for tag
                                        in categories]
                context['cat_hierarchy'] = [(node.name, node.category_name, node.category_path,
                                             self.site.link("category", node.category_name),
                                             node.indent_levels, node.indent_change_before,
                                             node.indent_change_after)
                                            for node in self.site.category_hierarchy]
            else:
                context["cat_items"] = None
            context["permalink"] = self.site.link("tag_index" if has_tags else "category_index", None, lang)
            context["description"] = context["title"]
            task = self.site.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            )
            task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.tags:page')]
            task['basename'] = str(self.name)
            yield task

    def list_tags_page(self, kw):
        """a global "all your tags/categories" page for each language"""
        if self.site.config['TAG_PATH'] == self.site.config['CATEGORY_PATH']:
            yield self._create_tags_page(kw, True, True)
        else:
            yield self._create_tags_page(kw, False, True)
            yield self._create_tags_page(kw, True, False)

    def _get_title(self, tag, is_category):
        if is_category:
            return self.site.parse_category_name(tag)[-1]
        else:
            return tag

    def _get_description(self, tag, is_category, kw, lang):
        descriptions = kw["category_pages_descriptions"] if is_category else kw["tag_pages_descriptions"]
        return descriptions[lang][tag] if lang in descriptions and tag in descriptions[lang] else None

    def _get_subcategories(self, category):
        node = self.site.category_hierarchy_lookup[category]
        return [(child.name, self.site.link("category", child.category_name)) for child in node.children]

    def tag_page_as_index(self, tag, lang, post_list, kw, is_category):
        """render a sort of index page collection using only this
        tag's posts."""

        kind = "category" if is_category else "tag"

        def page_link(i, displayed_i, num_pages, force_addition, extension=None):
            feed = "_atom" if extension == ".atom" else ""
            return utils.adjust_name_for_index_link(self.site.link(kind + feed, tag, lang), i, displayed_i, lang, self.site, force_addition, extension)

        def page_path(i, displayed_i, num_pages, force_addition, extension=None):
            feed = "_atom" if extension == ".atom" else ""
            return utils.adjust_name_for_index_path(self.site.path(kind + feed, tag, lang), i, displayed_i, lang, self.site, force_addition, extension)

        context_source = {}
        title = self._get_title(tag, is_category)
        if kw["generate_rss"]:
            # On a tag page, the feeds include the tag's feeds
            rss_link = ("""<link rel="alternate" type="application/rss+xml" """
                        """type="application/rss+xml" title="RSS for tag """
                        """{0} ({1})" href="{2}">""".format(
                            title, lang, self.site.link(kind + "_rss", tag, lang)))
            context_source['rss_link'] = rss_link
        if is_category:
            context_source["category"] = tag
            context_source["category_path"] = self.site.parse_category_name(tag)
        context_source["tag"] = title
        indexes_title = kw["messages"][lang]["Posts about %s"] % title
        context_source["description"] = self._get_description(tag, is_category, kw, lang)
        if is_category:
            context_source["subcategories"] = self._get_subcategories(tag)
        template_name = "tagindex.tmpl"

        yield self.site.generic_index_renderer(lang, post_list, indexes_title, template_name, context_source, kw, str(self.name), page_link, page_path)

    def tag_page_as_list(self, tag, lang, post_list, kw, is_category):
        """We render a single flat link list with this tag's posts"""
        kind = "category" if is_category else "tag"
        template_name = "tag.tmpl"
        output_name = os.path.join(kw['output_folder'], self.site.path(
            kind, tag, lang))
        context = {}
        context["lang"] = lang
        title = self._get_title(tag, is_category)
        if is_category:
            context["category"] = tag
            context["category_path"] = self.site.parse_category_name(tag)
        context["tag"] = title
        context["title"] = kw["messages"][lang]["Posts about %s"] % title
        context["posts"] = post_list
        context["permalink"] = self.site.link(kind, tag, lang)
        context["kind"] = kind
        context["description"] = self._get_description(tag, is_category, kw, lang)
        if is_category:
            context["subcategories"] = self._get_subcategories(tag)
        task = self.site.generic_post_list_renderer(
            lang,
            post_list,
            output_name,
            template_name,
            kw['filters'],
            context,
        )
        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.tags:list')]
        task['basename'] = str(self.name)
        yield task

    def tag_rss(self, tag, lang, posts, kw, is_category):
        """RSS for a single tag / language"""
        kind = "category" if is_category else "tag"
        # Render RSS
        output_name = os.path.normpath(
            os.path.join(kw['output_folder'],
                         self.site.path(kind + "_rss", tag, lang)))
        feed_url = urljoin(self.site.config['BASE_URL'], self.site.link(kind + "_rss", tag, lang).lstrip('/'))
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
                        (lang, "{0} ({1})".format(kw["blog_title"](lang), self._get_title(tag, is_category)),
                         kw["site_url"], None, post_list,
                         output_name, kw["rss_teasers"], kw["rss_plain"], kw['feed_length'],
                         feed_url, None, kw["rss_link_append_query"]))],
            'clean': True,
            'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.tags:rss')] + deps_uptodate,
            'task_dep': ['render_posts'],
        }
        return utils.apply_filters(task, kw['filters'])

    def slugify_tag_name(self, name):
        if self.site.config['SLUG_TAG_PATH']:
            name = utils.slugify(name)
        return name

    def tag_index_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'],
                              self.site.config['INDEX_FILE']] if _f]

    def category_index_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['CATEGORY_PATH'],
                              self.site.config['INDEX_FILE']] if _f]

    def tag_path(self, name, lang):
        if self.site.config['PRETTY_URLS']:
            return [_f for _f in [
                self.site.config['TRANSLATIONS'][lang],
                self.site.config['TAG_PATH'],
                self.slugify_tag_name(name),
                self.site.config['INDEX_FILE']] if _f]
        else:
            return [_f for _f in [
                self.site.config['TRANSLATIONS'][lang],
                self.site.config['TAG_PATH'],
                self.slugify_tag_name(name) + ".html"] if _f]

    def tag_atom_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], self.slugify_tag_name(name) + ".atom"] if
                _f]

    def tag_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], self.slugify_tag_name(name) + ".xml"] if
                _f]

    def slugify_category_name(self, name):
        path = self.site.parse_category_name(name)
        if self.site.config['CATEGORY_OUTPUT_FLAT_HIERARCHY']:
            path = path[-1:]  # only the leaf
        result = [self.slugify_tag_name(part) for part in path]
        result[0] = self.site.config['CATEGORY_PREFIX'] + result[0]
        if not self.site.config['PRETTY_URLS']:
            result = ['-'.join(result)]
        return result

    def _add_extension(self, path, extension):
        path[-1] += extension
        return path

    def category_path(self, name, lang):
        if self.site.config['PRETTY_URLS']:
            return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                  self.site.config['CATEGORY_PATH']] if
                    _f] + self.slugify_category_name(name) + [self.site.config['INDEX_FILE']]
        else:
            return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                  self.site.config['CATEGORY_PATH']] if
                    _f] + self._add_extension(self.slugify_category_name(name), ".html")

    def category_atom_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['CATEGORY_PATH']] if
                _f] + self._add_extension(self.slugify_category_name(name), ".atom")

    def category_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['CATEGORY_PATH']] if
                _f] + self._add_extension(self.slugify_category_name(name), ".xml")
