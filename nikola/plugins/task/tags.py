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

from __future__ import unicode_literals
import json
import os
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
        site.register_path_handler('tag_rss', self.tag_rss_path)
        site.register_path_handler('category', self.category_path)
        site.register_path_handler('category_rss', self.category_rss_path)
        return super(RenderTags, self).set_site(site)

    def gen_tasks(self):
        """Render the tag pages and feeds."""

        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "blog_title": self.site.config["BLOG_TITLE"],
            "site_url": self.site.config["SITE_URL"],
            "messages": self.site.MESSAGES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "tag_pages_are_indexes": self.site.config['TAG_PAGES_ARE_INDEXES'],
            "tag_pages_descriptions": self.site.config['TAG_PAGES_DESCRIPTIONS'],
            "category_pages_are_indexes": self.site.config['CATEGORY_PAGES_ARE_INDEXES'],
            "category_pages_descriptions": self.site.config['CATEGORY_PAGES_DESCRIPTIONS'],
            "index_display_post_count": self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "index_teasers": self.site.config['INDEX_TEASERS'],
            "generate_rss": self.site.config['GENERATE_RSS'],
            "rss_teasers": self.site.config["RSS_TEASERS"],
            "rss_plain": self.site.config["RSS_PLAIN"],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "feed_length": self.site.config['FEED_LENGTH'],
            "taglist_minimum_post_count": self.site.config['TAGLIST_MINIMUM_POSTS'],
            "tzinfo": self.site.tzinfo,
        }

        self.site.scan_posts()
        yield self.group_task()

        yield self.list_tags_page(kw)  # this also adds category and tag list to kw

        if not self.site.posts_per_tag and not self.site.posts_per_category:
            return

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

        for tag, posts in cat_list:
            if tag == '':  # This is uncategorized posts
                continue
            for task in render_lists(tag, posts, True):
                yield task

        # Tag cloud json file
        tag_cloud_data = {}
        for tag, posts in self.site.posts_per_tag.items():
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
        tags = list([tag for tag in self.site.posts_per_tag.keys()
                     if len(self.site.posts_per_tag[tag]) >= kw["taglist_minimum_post_count"]])
        categories = list(self.site.posts_per_category.keys())
        # We want our tags to be sorted case insensitive
        tags.sort(key=lambda a: a.lower())
        categories.sort(key=lambda a: a.lower())
        has_tags = (tags != ['']) and include_tags
        has_categories = (categories != ['']) and include_categories
        template_name = "tags.tmpl"
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

    def tag_page_as_index(self, tag, lang, post_list, kw, is_category):
        """render a sort of index page collection using only this
        tag's posts."""

        kind = "category" if is_category else "tag"

        def page_name(tagname, i, lang):
            """Given tag, n, returns a page name."""
            name = self.site.path(kind, tag, lang)
            if i:
                name = name.replace('.html', '-{0}.html'.format(i))
            return name

        # FIXME: deduplicate this with render_indexes
        template_name = "tagindex.tmpl"
        # Split in smaller lists
        lists = []
        while post_list:
            lists.append(post_list[:kw["index_display_post_count"]])
            post_list = post_list[kw["index_display_post_count"]:]
        num_pages = len(lists)
        for i, post_list in enumerate(lists):
            context = {}
            if kw["generate_rss"]:
                # On a tag page, the feeds include the tag's feeds
                rss_link = ("""<link rel="alternate" type="application/rss+xml" """
                            """type="application/rss+xml" title="RSS for tag """
                            """{0} ({1})" href="{2}">""".format(
                                tag, lang, self.site.link(kind + "_rss", tag, lang)))
                context['rss_link'] = rss_link
            output_name = os.path.join(kw['output_folder'],
                                       page_name(tag, i, lang))
            context["title"] = kw["messages"][lang][
                "Posts about %s"] % tag
            context["prevlink"] = None
            context["nextlink"] = None
            context['index_teasers'] = kw['index_teasers']
            if i > 1:
                context["prevlink"] = os.path.basename(
                    page_name(tag, i - 1, lang))
            if i == 1:
                context["prevlink"] = os.path.basename(
                    page_name(tag, 0, lang))
            if i < num_pages - 1:
                context["nextlink"] = os.path.basename(
                    page_name(tag, i + 1, lang))
            context["permalink"] = self.site.link(kind, tag, lang)
            context["tag"] = tag
            context["description"] = None
            descriptions = kw["category_pages_descriptions"] if is_category else kw["tag_pages_descriptions"]
            if lang in descriptions and tag in descriptions[lang]:
                context["description"] = descriptions[lang][tag]
            task = self.site.generic_post_list_renderer(
                lang,
                post_list,
                output_name,
                template_name,
                kw['filters'],
                context,
            )
            task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.tags:index')]
            task['basename'] = str(self.name)

            yield task

    def tag_page_as_list(self, tag, lang, post_list, kw, is_category):
        """We render a single flat link list with this tag's posts"""
        kind = "category" if is_category else "tag"
        template_name = "tag.tmpl"
        output_name = os.path.join(kw['output_folder'], self.site.path(
            kind, tag, lang))
        context = {}
        context["lang"] = lang
        context["title"] = kw["messages"][lang]["Posts about %s"] % tag
        context["posts"] = post_list
        context["permalink"] = self.site.link(kind, tag, lang)
        context["tag"] = tag
        context["kind"] = kind
        context["description"] = None
        if lang in kw["tag_pages_descriptions"] and tag in kw["tag_pages_descriptions"][lang]:
            context["description"] = kw["tag_pages_descriptions"][lang][tag]
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
                        (lang, "{0} ({1})".format(kw["blog_title"](lang), tag),
                         kw["site_url"], None, post_list,
                         output_name, kw["rss_teasers"], kw["rss_plain"], kw['feed_length'],
                         feed_url))],
            'clean': True,
            'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.tags:rss')] + deps_uptodate,
            'task_dep': ['render_posts'],
        }
        return utils.apply_filters(task, kw['filters'])

    def slugify_name(self, name):
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
                self.slugify_name(name),
                self.site.config['INDEX_FILE']] if _f]
        else:
            return [_f for _f in [
                self.site.config['TRANSLATIONS'][lang],
                self.site.config['TAG_PATH'],
                self.slugify_name(name) + ".html"] if _f]

    def tag_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], self.slugify_name(name) + ".xml"] if
                _f]

    def category_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['CATEGORY_PATH'], self.site.config['CATEGORY_PREFIX'] + self.slugify_name(name) + ".html"] if
                _f]

    def category_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['CATEGORY_PATH'], self.site.config['CATEGORY_PREFIX'] + self.slugify_name(name) + ".xml"] if
                _f]
