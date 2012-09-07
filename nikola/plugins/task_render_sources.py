import os

from nikola.plugin_categories import Task
from nikola import utils

class Sources(Task):
    """Copy page sources into the output."""

    name = "render_sources"

    def gen_tasks(self):
        """Publish the page sources into the output.

        Required keyword arguments:

        translations
        default_lang
        post_pages
        output_folder
        """
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "default_lang": self.site.config["DEFAULT_LANG"],
        }

        self.site.scan_posts()
        flag = False
        for lang in kw["translations"]:
            for post in self.site.timeline:
                output_name = os.path.join(kw['output_folder'],
                    post.destination_path(lang, post.source_ext()))
                source = post.source_path
                if lang != kw["default_lang"]:
                    source_lang = source + '.' + lang
                    if os.path.exists(source_lang):
                        source = source_lang
                yield {
                    'basename': 'render_sources',
                    'name': output_name.encode('utf8'),
                    'file_dep': [source],
                    'targets': [output_name],
                    'actions': [(utils.copy_file, (source, output_name))],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                    }
        if flag == False:  # No page rendered, yield a dummy task
            yield {
                'basename': 'render_sources',
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }
