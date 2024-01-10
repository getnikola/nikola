# -*- coding: utf-8 -*-

# Copyright © 2013-2024 Udo Spallek, Roberto Alsina and others.

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
"""Post list directive for reStructuredText."""

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from nikola import utils
from nikola.plugin_categories import RestExtension

# WARNING: the directive name is post-list
#          (with a DASH instead of an UNDERSCORE)


class Plugin(RestExtension):
    """Plugin for reST post-list directive."""

    name = "rest_post_list"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('post-list', PostListDirective)
        directives.register_directive('post_list', PostListDirective)
        PostListDirective.site = site
        return super().set_site(site)


class PostListDirective(Directive):
    """Provide a reStructuredText directive to create a list of posts."""

    option_spec = {
        'start': int,
        'stop': int,
        'reverse': directives.flag,
        'sort': directives.unchanged,
        'tags': directives.unchanged,
        'require_all_tags': directives.flag,
        'categories': directives.unchanged,
        'sections': directives.unchanged,
        'slugs': directives.unchanged,
        'post_type': directives.unchanged,
        'type': directives.unchanged,
        'lang': directives.unchanged,
        'template': directives.path,
        'id': directives.unchanged,
        'date': directives.unchanged,
    }

    def run(self):
        """Run post-list directive."""
        start = self.options.get('start')
        stop = self.options.get('stop')
        reverse = self.options.get('reverse', False)
        tags = self.options.get('tags')
        require_all_tags = 'require_all_tags' in self.options
        categories = self.options.get('categories')
        sections = self.options.get('sections')
        slugs = self.options.get('slugs')
        post_type = self.options.get('post_type')
        type = self.options.get('type', False)
        lang = self.options.get('lang', utils.LocaleBorg().current_lang)
        template = self.options.get('template', 'post_list_directive.tmpl')
        sort = self.options.get('sort')
        date = self.options.get('date')
        filename = self.state.document.settings._nikola_source_path

        output, deps = self.site.plugin_manager.get_plugin_by_name(
            'post_list', 'ShortcodePlugin').plugin_object.handler(
                start,
                stop,
                reverse,
                tags,
                require_all_tags,
                categories,
                sections,
                slugs,
                post_type,
                type,
                lang,
                template,
                sort,
                state=self.state,
                site=self.site,
                date=date,
                filename=filename)
        self.state.document.settings.record_dependencies.add(
            "####MAGIC####TIMELINE")
        for d in deps:
            self.state.document.settings.record_dependencies.add(d)
        if output:
            return [nodes.raw('', output, format='html')]
        else:
            return []
