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

from __future__ import unicode_literals
import codecs
import json
import os

from nikola.plugin_categories import Task
from nikola import utils


class RenderTags(Task):
    """Render the tag pages and feeds."""

    name = "render_tags"

    def gen_tasks(self):
        """Render the tag pages and feeds."""

        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "blog_title": self.site.config["BLOG_TITLE"],
            "site_url": self.site.config["SITE_URL"],
            "blog_description": self.site.config["BLOG_DESCRIPTION"],
            "messages": self.site.MESSAGES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "tag_pages_are_indexes": self.site.config['TAG_PAGES_ARE_INDEXES'],
            "index_display_post_count":
            self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "index_teasers": self.site.config['INDEX_TEASERS'],
            "rss_teasers": self.site.config["RSS_TEASERS"],
            "hide_untranslated_posts": self.site.config['HIDE_UNTRANSLATED_POSTS'],
        }

        self.site.scan_posts()

        yield self.list_tags_page(kw)

        if not self.site.posts_per_tag:
            yield {'basename': str(self.name), 'actions': []}
            return

        for tag, posts in list(self.site.posts_per_tag.items()):
            post_list = [self.site.global_data[post] for post in posts]
            post_list.sort(key=lambda a: a.date)
            post_list.reverse()
            for lang in kw["translations"]:
                if kw["hide_untranslated_posts"]:
                    filtered_posts = [x for x in post_list if x.is_translation_available(lang)]
                else:
                    filtered_posts = post_list
                rss_post_list = [p.post_name for p in filtered_posts]
                yield self.tag_rss(tag, lang, rss_post_list, kw)
                # Render HTML
                if kw['tag_pages_are_indexes']:
                    yield self.tag_page_as_index(tag, lang, filtered_posts, kw)
                else:
                    yield self.tag_page_as_list(tag, lang, filtered_posts, kw)

        # Tag cloud json file
        tag_cloud_data = {}
        for tag, posts in self.site.posts_per_tag.items():
            tag_cloud_data[tag] = [len(posts), self.site.link(
                'tag', tag, self.site.config['DEFAULT_LANG'])]
        output_name = os.path.join(kw['output_folder'],
                                   'assets', 'js', 'tag_cloud_data.json')

        def write_tag_data(data):
            try:
                os.makedirs(os.path.dirname(output_name))
            except:
                pass
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
        """a global "all your tags" page for each language"""
        tags = list(self.site.posts_per_tag.keys())
        # We want our tags to be sorted case insensitive
        tags.sort(key=lambda a: a.lower())
        template_name = "tags.tmpl"
        kw['tags'] = tags
        for lang in kw["translations"]:
            output_name = os.path.join(
                kw['output_folder'], self.site.path('tag_index', None, lang))
            output_name = output_name
            context = {}
            context["title"] = kw["messages"][lang]["Tags"]
            context["items"] = [(tag, self.site.link("tag", tag, lang)) for tag
                                in tags]
            context["permalink"] = self.site.link("tag_index", None, lang)
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
            yield task

    def tag_page_as_index(self, tag, lang, post_list, kw):
        """render a sort of index page collection using only this
        tag's posts."""

        def page_name(tagname, i, lang):
            """Given tag, n, returns a page name."""
            name = self.site.path("tag", tag, lang)
            if i:
                name = name.replace('.html', '-{0}.html'.format(i))
            return name

        # FIXME: deduplicate this with render_indexes
        template_name = "index.tmpl"
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
                            tag, lang, self.site.link("tag_rss", tag, lang)))
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
            context["permalink"] = self.site.link("tag", tag, lang)
            context["tag"] = tag
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

    def tag_page_as_list(self, tag, lang, post_list, kw):
        """We render a single flat link list with this tag's posts"""
        template_name = "tag.tmpl"
        output_name = os.path.join(kw['output_folder'], self.site.path(
            "tag", tag, lang))
        context = {}
        context["lang"] = lang
        context["title"] = kw["messages"][lang]["Posts about %s"] % tag
        context["posts"] = post_list
        context["permalink"] = self.site.link("tag", tag, lang)
        context["tag"] = tag
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

    def tag_rss(self, tag, lang, posts, kw):
        """RSS for a single tag / language"""
        #Render RSS
        output_name = os.path.join(kw['output_folder'],
                                   self.site.path("tag_rss", tag, lang))
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
                         kw["site_url"], kw["blog_description"], post_list,
                         output_name, kw["rss_teasers"]))],
            'clean': True,
            'uptodate': [utils.config_changed(kw)],
            'task_dep': ['render_posts'],
        }
