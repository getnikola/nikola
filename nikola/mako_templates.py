########################################
# Mako template handlers
########################################

import os

from mako.lookup import TemplateLookup

lookup = None


def get_template_lookup(directories):
    return TemplateLookup(
        directories=directories,
        module_directory='tmp',
        output_encoding='utf-8',
        )


def render_template(template_name, output_name, context, global_context):
    template = lookup.get_template(template_name)
    context.update(global_context)
    try:
        os.makedirs(os.path.dirname(output_name))
    except:
        pass
    with open(output_name, 'w+') as output:
        output.write(template.render(**context))


def template_deps(template_name):
    template = lookup.get_template(template_name)
    return [template.filename]
