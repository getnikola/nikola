import os

from nikola.plugin_categories import Task
from nikola.utils import config_changed


class Archive(Task):
    """Render the post archives."""

    name = "render_archive"

    def gen_tasks(self):
        kw = {
            "messages": self.site.MESSAGES,
            "translations": self.site.config['TRANSLATIONS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
        }

        # TODO add next/prev links for years
        template_name = "list.tmpl"
        # TODO: posts_per_year is global, kill it
        for year, posts in self.site.posts_per_year.items():
            for lang in kw["translations"]:
                output_name = os.path.join(
                    kw['output_folder'], self.site.path("archive", year, lang))
                post_list = [self.site.global_data[post] for post in posts]
                post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
                post_list.reverse()
                context = {}
                context["lang"] = lang
                context["items"] = [("[%s] %s" %
                    (post.date, post.title(lang)), post.permalink(lang))
                    for post in post_list]
                context["permalink"] = self.site.link("archive", year, lang)
                context["title"] = kw["messages"][lang]["Posts for year %s"]\
                    % year
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
                    task['basename'] = self.name
                    yield task

        # And global "all your years" page
        years = self.site.posts_per_year.keys()
        years.sort(reverse=True)
        template_name = "list.tmpl"
        kw['years'] = years
        for lang in kw["translations"]:
            context = {}
            output_name = os.path.join(
                kw['output_folder'], self.site.path("archive", None, lang))
            context["title"] = kw["messages"][lang]["Archive"]
            context["items"] = [(year, self.site.link("archive", year, lang))
                for year in years]
            context["permalink"] = self.site.link("archive", None, lang)
            for task in self.site.generic_post_list_renderer(
                lang,
                [],
                output_name,
                template_name,
                kw['filters'],
                context,
            ):
                task['uptodate'] = task.get('updtodate', []) +\
                    [config_changed(kw)]
                task['basename'] = self.name
                yield task
