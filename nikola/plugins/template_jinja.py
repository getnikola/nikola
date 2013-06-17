# Copyright (c) 2012 Roberto Alsina y otros.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Jinja template handlers"""

import os
import json
from collections import deque
try:
    import jinja2
    from jinja2 import meta
except ImportError:
    jinja2 = None  # NOQA

from nikola.plugin_categories import TemplateSystem


class JinjaTemplates(TemplateSystem):
    """Wrapper for Jinja2 templates."""

    name = "jinja"
    lookup = None
    dependency_cache = {}

    def __init__(self):
        """ initialize Jinja2 wrapper with extended set of filters"""
        if jinja2 is None:
            return
        self.lookup = jinja2.Environment()
        self.lookup.filters['tojson'] = json.dumps

    def set_directories(self, directories, cache_folder):
        """Createa  template lookup."""
        if jinja2 is None:
            raise Exception('To use this theme you need to install the '
                            '"Jinja2" package.')
        self.lookup.loader = jinja2.FileSystemLoader(directories,
                                                     encoding='utf-8')

    def render_template(self, template_name, output_name, context):
        """Render the template into output_name using context."""
        if jinja2 is None:
            raise Exception('To use this theme you need to install the '
                            '"Jinja2" package.')
        template = self.lookup.get_template(template_name)
        output = template.render(**context)
        if output_name is not None:
            try:
                os.makedirs(os.path.dirname(output_name))
            except:
                pass
            with open(output_name, 'w+') as output:
                output.write(output.encode('utf8'))
        return output

    def template_deps(self, template_name):
        # Cache the lists of dependencies for each template name.
        if self.dependency_cache.get(template_name) is None:
            # Use a breadth-first search to find all templates this one
            # depends on.
            queue = deque([template_name])
            visited_templates = set([template_name])
            deps = []
            while len(queue) > 0:
                curr = queue.popleft()
                source, filename = self.lookup.loader.get_source(self.lookup,
                                                                 curr)[:2]
                deps.append(filename)
                ast = self.lookup.parse(source)
                dep_names = meta.find_referenced_templates(ast)
                for dep_name in dep_names:
                    if (dep_name not in visited_templates
                            and dep_name is not None):
                        visited_templates.add(dep_name)
                        queue.append(dep_name)
            self.dependency_cache[template_name] = deps
        return self.dependency_cache[template_name]
