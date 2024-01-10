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

"""Mako template handler."""

import io
import os
import re
import shutil

from mako import exceptions, util, lexer, parsetree
from mako.lookup import TemplateLookup
from mako.template import Template
from markupsafe import Markup  # It's ok, Mako requires it

from nikola.plugin_categories import TemplateSystem
from nikola.utils import makedirs, get_logger

LOGGER = get_logger('mako')


class MakoTemplates(TemplateSystem):
    """Support for Mako templates."""

    name = "mako"

    lookup = None
    cache = {}
    filters = {}
    directories = []
    cache_dir = None

    def get_string_deps(self, text, context=None, *, filename=None):
        """Find dependencies for a template string."""
        lex = lexer.Lexer(text=text, filename=filename, input_encoding='utf-8')
        lex.parse()

        deps = []
        for n in lex.template.nodes:
            keyword = getattr(n, 'keyword', None)
            if keyword in ["inherit", "namespace"] or isinstance(n, parsetree.IncludeTag):
                filename = n.attributes["file"]
                if '${' in filename:
                    # Support for comment helper inclusions
                    filename = re.sub(r'''\${context\[['"](.*?)['"]]}''', lambda m: context[m.group(1)], filename)
                deps.append(filename)
        # Some templates will include "foo.tmpl" and we need paths, so normalize them
        # using the template lookup
        for i, d in enumerate(deps):
            dep = self.get_template_path(d)
            if dep:
                deps[i] = dep
            else:
                LOGGER.error("Cannot find template {0} referenced in {1}",
                             d, filename)
        return deps

    def get_deps(self, filename, context=None):
        """Get paths to dependencies for a template."""
        text = util.read_file(filename)
        return self.get_string_deps(text, context, filename=filename)

    def set_directories(self, directories, cache_folder):
        """Create a new template lookup with set directories."""
        cache_dir = os.path.join(cache_folder, '.mako.tmp')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        self.directories = directories
        self.cache_dir = cache_dir
        self.create_lookup()

    def inject_directory(self, directory):
        """Add a directory to the lookup and recreate it if it's not there yet."""
        if directory not in self.directories:
            self.directories.append(directory)
            self.create_lookup()

    def create_lookup(self):
        """Create a template lookup."""
        self.lookup = TemplateLookup(
            directories=self.directories,
            module_directory=self.cache_dir,
            input_encoding='utf-8',
            output_encoding='utf-8')

    def set_site(self, site):
        """Set the Nikola site."""
        self.site = site
        self.filters.update(self.site.config['TEMPLATE_FILTERS'])

    def render_template(self, template_name, output_name, context):
        """Render the template into output_name using context."""
        context['striphtml'] = striphtml
        template = self.lookup.get_template(template_name)
        data = template.render_unicode(**context)
        if output_name is not None:
            makedirs(os.path.dirname(output_name))
            with io.open(output_name, 'w', encoding='utf-8') as output:
                output.write(data)
        return data

    def render_template_to_string(self, template, context):
        """Render template to a string using context."""
        context.update(self.filters)
        return Template(template, lookup=self.lookup).render(**context)

    def template_deps(self, template_name, context=None):
        """Generate list of dependencies for a template."""
        # We can cache here because dependencies should
        # not change between runs
        if self.cache.get(template_name, None) is None:
            template = self.lookup.get_template(template_name)
            dep_filenames = self.get_deps(template.filename, context)
            deps = [template.filename]
            for fname in dep_filenames:
                # yes, it uses forward slashes on Windows
                deps += self.template_deps(fname.split('/')[-1], context)
            self.cache[template_name] = list(set(deps))
        return self.cache[template_name]

    def get_template_path(self, template_name):
        """Get the path to a template or return None."""
        try:
            t = self.lookup.get_template(template_name)
            return t.filename
        except exceptions.TopLevelLookupException:
            return None


def striphtml(text):
    """Strip HTML tags from text."""
    return Markup(text).striptags()
