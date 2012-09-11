
from nikola.plugin_categories import Task


class RenderPages(Task):
    """Render pages into output."""

    name = "render_pages"

    def gen_task(self):
        """Build final pages from metadata and HTML fragments."""
        kw = {
            "post_pages": self.site.config["post_pages"],
            "filters": self.site.config["filters"],
        }
        self.site.scan_posts()
        flag = False
        for lang in kw["translations"]:
            for wildcard, destination, template_name, _ in kw["post_pages"]:
                for task in self.site.generic_page_renderer(lang,
                    wildcard, template_name, destination, kw["filters"]):
                    # TODO: enable or remove
                    #task['uptodate'] = task.get('uptodate', []) +\
                        #[config_changed(kw)]
                    task['basename'] = 'render_pages'
                    flag = True
                    yield task
        if flag is False:  # No page rendered, yield a dummy task
            yield {
                'basename': 'render_pages',
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }
