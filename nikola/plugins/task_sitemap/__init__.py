import os
import tempfile

from nikola.plugin_categories import LateTask
from nikola.utils import config_changed

import sitemap_gen as smap

class Sitemap(LateTask):
    """Copy theme assets into output."""

    name = "sitemap"

    def gen_tasks(self):
        """Generate Google sitemap."""
        kw = {
            "blog_url": self.site.config["BLOG_URL"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
        }
        output_path = os.path.abspath(kw['output_folder'])
        sitemap_path = os.path.join(output_path, "sitemap.xml.gz")

        def sitemap():
            # Generate config
            config_data = """<?xml version="1.0" encoding="UTF-8"?>
    <site
    base_url="%s"
    store_into="%s"
    verbose="1" >
    <directory path="%s" url="%s" />
    <filter action="drop" type="wildcard" pattern="*~" />
    <filter action="drop" type="regexp" pattern="/\.[^/]*" />
    </site>""" % (
                kw["blog_url"],
                sitemap_path,
                output_path,
                kw["blog_url"],
            )
            config_file = tempfile.NamedTemporaryFile(delete=False)
            config_file.write(config_data)
            config_file.close()

            # Generate sitemap
            sitemap = smap.CreateSitemapFromFile(config_file.name, True)
            if not sitemap:
                smap.output.Log('Configuration file errors -- exiting.', 0)
            else:
                sitemap.Generate()
                smap.output.Log('Number of errors: %d' %
                    smap.output.num_errors, 1)
                smap.output.Log('Number of warnings: %d' %
                    smap.output.num_warns, 1)
            os.unlink(config_file.name)

        yield {
            "basename": "sitemap",
            "targets": [sitemap_path],
            "actions": [(sitemap,)],
            "uptodate": [config_changed(kw)],
            "clean": True,
        }
