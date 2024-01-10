# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

"""Jinja template handler."""

import io
import json
import os

from nikola.plugin_categories import TemplateSystem
from nikola.utils import makedirs, req_missing, slugify, sort_posts, _smartjoin_filter

try:
    import jinja2
    import jinja2.nodes
    from jinja2 import meta
except ImportError:
    jinja2 = None


class JinjaTemplates(TemplateSystem):
    """Support for Jinja2 templates."""

    name = "jinja"
    lookup = None
    dependency_cache = {}
    per_file_cache = {}

    def __init__(self):
        """Initialize Jinja2 environment with extended set of filters."""
        if jinja2 is None:
            return

    def set_directories(self, directories, cache_folder):
        """Create a new template lookup with set directories."""
        if jinja2 is None:
            req_missing(['jinja2'], 'use this theme')
        cache_folder = os.path.join(cache_folder, 'jinja')
        makedirs(cache_folder)
        cache = jinja2.FileSystemBytecodeCache(cache_folder)
        self.lookup = jinja2.Environment(bytecode_cache=cache)
        self.lookup.trim_blocks = True
        self.lookup.lstrip_blocks = True
        self.lookup.filters['tojson'] = json.dumps
        self.lookup.filters['sort_posts'] = sort_posts
        self.lookup.filters['smartjoin'] = _smartjoin_filter
        self.lookup.filters['slugify'] = slugify
        self.lookup.globals['enumerate'] = enumerate
        self.lookup.globals['isinstance'] = isinstance
        self.lookup.globals['tuple'] = tuple
        self.directories = directories
        self.create_lookup()

    def inject_directory(self, directory):
        """Add a directory to the lookup and recreate it if it's not there yet."""
        if directory not in self.directories:
            self.directories.append(directory)
            self.create_lookup()

    def create_lookup(self):
        """Create a template lookup."""
        self.lookup.loader = jinja2.FileSystemLoader(self.directories,
                                                     encoding='utf-8')

    def set_site(self, site):
        """Set the Nikola site."""
        self.site = site
        self.lookup.filters.update(self.site.config['TEMPLATE_FILTERS'])

    def render_template(self, template_name, output_name, context):
        """Render the template into output_name using context."""
        if jinja2 is None:
            req_missing(['jinja2'], 'use this theme')
        template = self.lookup.get_template(template_name)
        data = template.render(**context)
        if output_name is not None:
            makedirs(os.path.dirname(output_name))
            with io.open(output_name, 'w', encoding='utf-8') as output:
                output.write(data)
        return data

    def render_template_to_string(self, template, context):
        """Render template to a string using context."""
        return self.lookup.from_string(template).render(**context)

    def get_string_deps(self, text, context=None):
        """Find dependencies for a template string."""
        deps = set([])
        ast = self.lookup.parse(text)
        simple_dep_names = [d for d in meta.find_referenced_templates(ast) if d]
        formatted_dep_names = [
            imp.template.left.value % (context[imp.template.right.name],)
            for imp in ast.find_all(jinja2.nodes.Import)
            if isinstance(imp.template, jinja2.nodes.Mod)
        ]
        dep_names = simple_dep_names + formatted_dep_names
        for dep_name in dep_names:
            filename = self.lookup.loader.get_source(self.lookup, dep_name)[1]
            sub_deps = [filename] + self.get_deps(filename, context)
            self.dependency_cache[dep_name] = sub_deps
            deps |= set(sub_deps)
        return list(deps)

    def get_deps(self, filename, context=None):
        """Return paths to dependencies for the template loaded from filename."""
        with io.open(filename, 'r', encoding='utf-8-sig') as fd:
            text = fd.read()
        return self.get_string_deps(text, context)

    def template_deps(self, template_name, context=None):
        """Generate list of dependencies for a template."""
        if self.dependency_cache.get(template_name) is None:
            filename = self.lookup.loader.get_source(self.lookup, template_name)[1]
            self.dependency_cache[template_name] = [filename] + self.get_deps(filename, context)
        return self.dependency_cache[template_name]

    def get_template_path(self, template_name):
        """Get the path to a template or return None."""
        try:
            t = self.lookup.get_template(template_name)
            return t.filename
        except jinja2.TemplateNotFound:
            return None
