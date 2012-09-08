"""Jinja template handlers"""

import os
import jinja2

from nikola.plugin_categories import TemplateSystem


class JinjaTemplates(TemplateSystem):
    """Wrapper for Jinja2 templates."""

    name = "jinja"
    lookup = None

    def set_directories(self, directories):
        """Createa  template lookup."""
        self.lookup = jinja2.Environment(loader=jinja2.FileSystemLoader(
            directories,
            encoding='utf-8',
            ))

    def render_template(self, template_name, output_name, context,
        global_context):
        """Render the template into output_name using context."""

        template = self.lookup.get_template(template_name)
        local_context = {}
        local_context["template_name"] = template_name
        local_context.update(global_context)
        local_context.update(context)
        output = template.render(**local_context)
        if output_name is not None:
            try:
                os.makedirs(os.path.dirname(output_name))
            except:
                pass
            with open(output_name, 'w+') as output:
                output.write(output.encode('utf8'))
        return output

    def template_deps(self, template_name):
        # FIXME: unimplemented
        return []
