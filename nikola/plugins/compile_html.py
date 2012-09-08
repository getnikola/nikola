"""Implementation of compile_html based on markdown."""

import os
import shutil


from nikola.plugin_categories import PageCompiler


class CompileHtml(PageCompiler):
    """Compile HTML into HTML."""

    name = "html"

    def compile_html(self, source, dest):
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        shutil.copyfile(source, dest)
