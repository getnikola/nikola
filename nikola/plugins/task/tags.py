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
import codecs
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
            "index_display_post_count":
            self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "index_teasers": self.site.config['INDEX_TEASERS'],
            "rss_teasers": self.site.config["RSS_TEASERS"],
            "hide_untranslated_posts": self.site.config['HIDE_UNTRANSLATED_POSTS'],
            "feed_length": self.site.config['FEED_LENGTH'],
        }

        self.site.scan_posts()
        yield self.group_task()

        yield self.list_tags_page(kw)

        if not self.site.posts_per_tag and not self.site.posts_per_category:
            return

        tag_list = list(self.site.posts_per_tag.items())
        cat_list = list(self.site.posts_per_category.items())

        def render_lists(tag, posts, is_category=True):
            post_list = [self.site.global_data[post] for post in posts]
            post_list.sort(key=lambda a: a.date)
            post_list.reverse()
            for lang in kw["translations"]:
                if kw["hide_untranslated_posts"]:
                    filtered_posts = [x for x in post_list if x.is_translation_available(lang)]
                else:
                    filtered_posts = post_list
                rss_post_list = [p.source_path for p in filtered_posts]
                yield self.tag_rss(tag, lang, rss_post_list, kw, is_category)
                # Render HTML
                if kw['tag_pages_are_indexes']:
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
                                     'url': post.base_path.replace('cache', '')}
                                    for post in reversed(sorted(self.site.timeline, key=lambda post: post.date))
                                    if tag in post.alltags])
            tag_cloud_data[tag] = [len(posts), self.site.link(
                'tag', tag, self.site.config['DEFAULT_LANG']), tag_posts]
        output_name = os.path.join(kw['output_folder'],
                                   'assets', 'js', 'tag_cloud_data.json')

        def write_tag_data(data):
            utils.makedirs(os.path.dirname(output_name))
            with codecs.open(output_name, 'wb+', 'utf8') as fd:
                fd.write(json.dumps(data))

        task = {
            'basename': str(self.name),
            'name': str(output_name)
        }

        task['uptodate'] = [utils.config_changed(tag_cloud_data)]
        task['targets'] = [output_name]
        task['actions'] = [(write_tag_data, [tag_cloud_data])]
        task['clean'] = True
        yield task

    def list_tags_page(self, kw):
        """a global "all your tags/categories" page for each language"""
        tags = list(self.site.posts_per_tag.keys())
        categories = list(self.site.posts_per_category.keys())
        # We want our tags to be sorted case insensitive
        tags.sort(key=lambda a: a.lower())
        categories.sort(key=lambda a: a.lower())
        if categories != ['']:
            has_categories = True
        else:
            has_categories = False
        template_name = "tags.tmpl"
        kw['tags'] = tags
        kw['categories'] = categories
        for lang in kw["translations"]:
            output_name = os.path.join(
                kw['output_folder'], self.site.path('tag_index', None, lang))
            output_name = output_name
            context = {}
            if has_categories:
                context["title"] = kw["messages"][lang]["Tags and Categories"]
            else:
                context["title"] = kw["messages"][lang]["Tags"]
            context["items"] = [(tag, self.site.link("tag", tag, lang)) for tag
                                in tags]
            if has_categories:
                context["cat_items"] = [(tag, self.site.link("category", tag, lang)) for tag
                                        in categories]
            else:
                context["cat_items"] = None
            context["permalink"] = self.site.link("tag_index", None, lang)
            context["description"] = None
            task = self.site.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            )
            task_cfg = {1: task['uptodate'][0].config, 2: kw}
            task['uptodate'] = [utils.config_changed(task_cfg)]
            task['basename'] = str(self.name)
            yield task

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
            task = self.site.generic_post_list_renderer(
                lang,
                post_list,
                output_name,
                template_name,
                kw['filters'],
                context,
            )
            task_cfg = {1: task['uptodate'][0].config, 2: kw}
            task['uptodate'] = [utils.config_changed(task_cfg)]
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
        task = self.site.generic_post_list_renderer(
            lang,
            post_list,
            output_name,
            template_name,
            kw['filters'],
            context,
        )
        task_cfg = {1: task['uptodate'][0].config, 2: kw}
        task['uptodate'] = [utils.config_changed(task_cfg)]
        task['basename'] = str(self.name)
        yield task

    def tag_rss(self, tag, lang, posts, kw, is_category):
        """RSS for a single tag / language"""
        kind = "category" if is_category else "tag"
        #Render RSS
        output_name = os.path.normpath(
            os.path.join(kw['output_folder'],
                         self.site.path(kind + "_rss", tag, lang)))
        feed_url = urljoin(self.site.config['BASE_URL'], self.site.link(kind + "_rss", tag, lang).lstrip('/'))
        deps = []
        post_list = [self.site.global_data[post] for post in posts if
                     self.site.global_data[post].use_in_feeds]
        post_list.sort(key=lambda a: a.date)
        post_list.reverse()
        for post in post_list:
            deps += post.deps(lang)
        return {
            'basename': str(self.name),
            'name': output_name,
            'file_dep': deps,
            'targets': [output_name],
            'actions': [(utils.generic_rss_renderer,
                        (lang, "{0} ({1})".format(kw["blog_title"], tag),
                         kw["site_url"], None, post_list,
                         output_name, kw["rss_teasers"], kw['feed_length'], feed_url))],
            'clean': True,
            'uptodate': [utils.config_changed(kw)],
            'task_dep': ['render_posts'],
        }

    def slugify_name(self, name):
        if self.site.config['SLUG_TAG_PATH']:
            name = utils.slugify(name)
        return name

    def tag_index_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'],
                              self.site.config['INDEX_FILE']] if _f]

    def tag_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], self.slugify_name(name) + ".html"] if
                _f]

    def tag_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], self.slugify_name(name) + ".xml"] if
                _f]

    def category_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], "cat_" + self.slugify_name(name) + ".html"] if
                _f]

    def category_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], "cat_" + self.slugify_name(name) + ".xml"] if
                _f]
