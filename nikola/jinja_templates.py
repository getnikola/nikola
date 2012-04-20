########################################
# Jinja template handlers
########################################

import os

import jinja2

lookup = None

def get_template_lookup(themes):
    return jinja2.FileSystemLoader(
        [os.path.join('themes', name, "templates") for name in themes],
        encoding='utf-8',
        )

def render_template(template, output_name, context, global_context):
    context.update(global_context)
    try:
        os.makedirs(os.path.dirname(output_name))
    except:
        pass
    with open(output_name, 'w+') as output:
        output.write(template.render(**context))
