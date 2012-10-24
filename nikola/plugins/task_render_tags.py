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
            "blog_url": self.site.config["BLOG_URL"],
            "blog_description": self.site.config["BLOG_DESCRIPTION"],
            "messages": self.site.MESSAGES,
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "tag_pages_are_indexes": self.site.config['TAG_PAGES_ARE_INDEXES'],
            "index_display_post_count":
                self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "index_teasers": self.site.config['INDEX_TEASERS'],
        }

        self.site.scan_posts()

        if not self.site.posts_per_tag:
            yield {
                    'basename': self.name,
                    'actions': [],
                }
            return

        def page_name(tagname, i, lang):
            """Given tag, n, returns a page name."""
            name = self.site.path("tag", tag, lang)
            if i:
                name = name.replace('.html', '-%s.html' % i)
            return name

        for tag, posts in self.site.posts_per_tag.items():
            post_list = [self.site.global_data[post] for post in posts]
            post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
            post_list.reverse()
            for lang in kw["translations"]:
                #Render RSS
                output_name = os.path.join(kw['output_folder'],
                    self.site.path("tag_rss", tag, lang))
                deps = []
                post_list = [self.site.global_data[post] for post in posts
                    if self.site.global_data[post].use_in_feeds]
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
                    'uptodate': [utils.config_changed(kw)],
                    'basename': self.name
                }

                # Render HTML
                if kw['tag_pages_are_indexes']:
                    # We render a sort of index page collection using only
                    # this tag's posts.

                    # FIXME: deduplicate this with render_indexes
                    template_name = "index.tmpl"
                    # Split in smaller lists
                    lists = []
                    while post_list:
                        lists.append(post_list[
                            :kw["index_display_post_count"]])
                        post_list = post_list[
                            kw["index_display_post_count"]:]
                    num_pages = len(lists)
                    for i, post_list in enumerate(lists):
                        context = {}
                        # On a tag page, the feeds include the tag's feeds
                        rss_link = \
                        """<link rel="alternate" type="application/rss+xml" """\
                        """type="application/rss+xml" title="RSS for tag """\
                        """%s (%s)" href="%s">""" % \
                            (tag, lang, self.site.link("tag_rss", tag, lang))
                        context['rss_link'] = rss_link
                        output_name = os.path.join(kw['output_folder'],
                            page_name(tag, i, lang))
                        context["title"] = kw["messages"][lang][
                            u"Posts about %s"] % tag
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
                        for task in self.site.generic_post_list_renderer(
                            lang,
                            post_list,
                            output_name,
                            template_name,
                            kw['filters'],
                            context,
                        ):
                            task['uptodate'] = [utils.config_changed({
                                1: task['uptodate'][0].config,
                                2: kw})]
                            task['basename'] = self.name
                            yield task
                else:
                    # We render a single flat link list with this tag's posts
                    template_name = "tag.tmpl"
                    output_name = os.path.join(kw['output_folder'],
                        self.site.path("tag", tag, lang))
                    context = {}
                    context["lang"] = lang
                    context["title"] = kw["messages"][lang][
                        u"Posts about %s"] % tag
                    context["items"] = [("[%s] %s" % (post.date,
                        post.title(lang)),
                        post.permalink(lang)) for post in post_list]
                    context["permalink"] = self.site.link("tag", tag, lang)
                    context["tag"] = tag
                    for task in self.site.generic_post_list_renderer(
                        lang,
                        post_list,
                        output_name,
                        template_name,
                        kw['filters'],
                        context,
                    ):
                        task['uptodate'] = [utils.config_changed({
                            1: task['uptodate'][0].config,
                            2: kw})]
                        task['basename'] = self.name
                        yield task

        # And global "all your tags" page
        tags = self.site.posts_per_tag.keys()
        tags.sort()
        template_name = "tags.tmpl"
        kw['tags'] = tags
        for lang in kw["translations"]:
            output_name = os.path.join(
                kw['output_folder'], self.site.path('tag_index', None, lang))
            context = {}
            context["title"] = kw["messages"][lang][u"Tags"]
            context["items"] = [(tag, self.site.link("tag", tag, lang))
                for tag in tags]
            context["permalink"] = self.site.link("tag_index", None, lang)
            for task in self.site.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            ):
                task['uptodate'] = [utils.config_changed({
                    1: task['uptodate'][0].config,
                    2: kw})]
                yield task
