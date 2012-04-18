########################################
# Mako template handlers
########################################

import os

from mako.lookup import TemplateLookup
from mako.template import Template

def get_template_lookup(themes):
    return TemplateLookup(
        directories=[os.path.join('themes', name, "templates") for name in themes],
        module_directory='tmp',
        output_encoding='utf-8',
        )

def render_template(template, output_name, context, global_context):
    context.update(global_context)
    try:
        os.makedirs(os.path.dirname(output_name))
    except:
        pass
    with open(output_name, 'w+') as output:
        output.write(template.render(**context))
