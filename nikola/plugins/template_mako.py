"""Mako template handlers"""

import os
import shutil

from mako import util, lexer
from mako.lookup import TemplateLookup

from nikola.plugin_categories import TemplateSystem


class MakoTemplates(TemplateSystem):
    """Wrapper for Mako templates."""

    name = "mako"

    lookup = None
    cache = {}

    def get_deps(self, filename):
        text = util.read_file(filename)
        lex = lexer.Lexer(text=text, filename=filename)
        lex.parse()

        deps = []
        for n in lex.template.nodes:
            if getattr(n, 'keyword', None) == "inherit":
                deps.append(n.attributes['file'])
            # TODO: include tags are not handled
        return deps

    def set_directories(self, directories, cache_folder):
        """Createa  template lookup."""
        cache_dir = os.path.join(cache_folder, '.mako.tmp')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        self.lookup = TemplateLookup(
            directories=directories,
            module_directory=cache_dir,
            output_encoding='utf-8',
            )

    def render_template(self, template_name, output_name, context):
        """Render the template into output_name using context."""

        template = self.lookup.get_template(template_name)
        data = template.render_unicode(**context)
        if output_name is not None:
            try:
                os.makedirs(os.path.dirname(output_name))
            except:
                pass
            with open(output_name, 'w+') as output:
                output.write(data)
        return data

    def template_deps(self, template_name):
        """Returns filenames which are dependencies for a template."""
        # We can cache here because depedencies should
        # not change between runs
        if self.cache.get(template_name, None) is None:
            template = self.lookup.get_template(template_name)
            dep_filenames = self.get_deps(template.filename)
            deps = [template.filename]
            for fname in dep_filenames:
                deps += self.template_deps(fname)
            self.cache[template_name] = tuple(deps)
        return list(self.cache[template_name])
