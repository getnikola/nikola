import os

from nikola import utils
from nikola.plugin_categories import Task


class RenderRSS(Task):
    """Generate RSS feeds."""

    name = "render_pages"

    def gen_tasks(self):
        """Generate RSS feeds."""
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "filters": self.site.config["FILTERS"],
            "blog_title": self.site.config["BLOG_TITLE"],
            "blog_url": self.site.config["BLOG_URL"],
            "blog_description": self.site.config["BLOG_DESCRIPTION"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
        }
        self.site.scan_posts()
        # TODO: timeline is global, kill it
        for lang in kw["translations"]:
            output_name = os.path.join(kw['output_folder'],
                self.site.path("rss", None, lang))
            deps = []
            posts = [x for x in self.site.timeline if x.use_in_feeds][:10]
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
                'uptodate': [utils.config_changed(kw)],
            }
