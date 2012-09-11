from copy import copy
import os

from nikola.plugin_categories import Task
from nikola import utils


class RenderPosts(Task):
    """Build HTML fragments from metadata and text."""

    name = "render_posts"

    def gen_tasks(self):
        """Build HTML fragments from metadata and text."""
        self.site.scan_posts()
        kw = {
            "translations": self.site.config["translations"],
            "timeline": self.site.timeline,
            "default_lang": self.site.config["DEFAULT_LANG"],
        }

        flag = False
        for lang in kw["translations"]:
            # TODO: timeline is global, get rid of it
            deps_dict = copy(kw)
            deps_dict.pop('timeline')
            for post in kw['timeline']:
                source = post.source_path
                dest = post.base_path
                if lang != kw["default_lang"]:
                    dest += '.' + lang
                    source_lang = source + '.' + lang
                    if os.path.exists(source_lang):
                        source = source_lang
                flag = True
                yield {
                    'basename': self.name,
                    'name': dest.encode('utf-8'),
                    'file_dep': post.fragment_deps(lang),
                    'targets': [dest],
                    'actions': [(self.site.get_compiler(post.source_path),
                        [source, dest])],
                    'clean': True,
                    'uptodate': [utils.config_changed(deps_dict)],
                }
        if flag is False:  # Return a dummy task
            yield {
                'basename': self.name,
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }
