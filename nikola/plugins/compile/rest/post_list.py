# -*- coding: utf-8 -*-

# Copyright © 2013-2018 Udo Spallek, Roberto Alsina and others.

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

# from nikola.plugins.shortcode.post_list import _do_post_list

# WARNING: the directive name is post-list
#          (with a DASH instead of an UNDERSCORE)


class Plugin(RestExtension):
    """Plugin for reST post-list directive."""

    name = "rest_post_list"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('post-list', PostList)
        PostList.site = site
        return super(Plugin, self).set_site(site)


class PostList(Directive):
    """Provide a reStructuredText directive to create a list of posts.

    Post List
    =========
    :Directive Arguments: None.
    :Directive Options: lang, start, stop, reverse, sort, date, tags, categories, sections, slugs, post_type, template, id
    :Directive Content: None.

    The posts appearing in the list can be filtered by options.
    *List slicing* is provided with the *start*, *stop* and *reverse* options.

    The following not required options are recognized:

    ``start`` : integer
        The index of the first post to show.
        A negative value like ``-3`` will show the *last* three posts in the
        post-list.
        Defaults to None.

    ``stop`` : integer
        The index of the last post to show.
        A value negative value like ``-1`` will show every post, but not the
        *last* in the post-list.
        Defaults to None.

    ``reverse`` : flag
        Reverse the order of the post-list.
        Defaults is to not reverse the order of posts.

    ``sort`` : string
        Sort post list by one of each post's attributes, usually ``title`` or a
        custom ``priority``.  Defaults to None (chronological sorting).

    ``date`` : string
        Show posts that match date range specified by this option. Format:

        * comma-separated clauses (AND)
        * clause: attribute comparison_operator value (spaces optional)
          * attribute: year, month, day, hour, month, second, weekday, isoweekday; or empty for full datetime
          * comparison_operator: == != <= >= < >
          * value: integer, 'now' or dateutil-compatible date input

    ``tags`` : string [, string...]
        Filter posts to show only posts having at least one of the ``tags``.
        Defaults to None.

    ``require_all_tags`` : flag
        Change tag filter behaviour to show only posts that have all specified ``tags``.
        Defaults to False.

    ``categories`` : string [, string...]
        Filter posts to show only posts having one of the ``categories``.
        Defaults to None.

    ``sections`` : string [, string...]
        Filter posts to show only posts having one of the ``sections``.
        Defaults to None.

    ``slugs`` : string [, string...]
        Filter posts to show only posts having at least one of the ``slugs``.
        Defaults to None.

    ``post_type`` (or ``type``) : string
        Show only ``posts``, ``pages`` or ``all``.
        Replaces ``all``. Defaults to ``posts``.

    ``lang`` : string
        The language of post *titles* and *links*.
        Defaults to default language.

    ``template`` : string
        The name of an alternative template to render the post-list.
        Defaults to ``post_list_directive.tmpl``

    ``id`` : string
        A manual id for the post list.
        Defaults to a random name composed by 'post_list_' + uuid.uuid4().hex.
    """

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

        output, deps = self.site.plugin_manager.getPluginByName(
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
