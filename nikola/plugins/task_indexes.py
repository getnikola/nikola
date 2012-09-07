import os

from nikola.plugin_categories import Task
from nikola.utils import config_changed


class Indexes(Task):
    """Render the blog indexes."""

    name = "render_indexes"

    def gen_tasks(self):
        self.site.scan_posts()

        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "index_display_post_count":
                self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "messages": self.site.MESSAGES,
            "index_teasers": self.site.config['INDEX_TEASERS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
        }

        template_name = "index.tmpl"
        # TODO: timeline is global, get rid of it
        posts = [x for x in self.site.timeline if x.use_in_feeds]
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
                if self.site.config.get("INDEXES_TITLE", ""):
                    indexes_title = self.site.config['INDEXES_TITLE']
                else:
                    indexes_title = self.site.config["BLOG_TITLE"]
                if not i:
                    output_name = "index.html"
                    context["title"] = indexes_title
                else:
                    output_name = "index-%s.html" % i
                    if self.site.config.get("INDEXES_PAGES", ""):
                        indexes_pages = self.site.config["INDEXES_PAGES"] % i
                    else:
                        indexes_pages = " (" + \
                            kw["messages"][lang]["old posts page %d"] % i + ")"
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
                context["permalink"] = self.site.link("index", i, lang)
                output_name = os.path.join(
                    kw['output_folder'], self.site.path("index", i, lang))
                for task in self.site.generic_post_list_renderer(
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
