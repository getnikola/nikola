# -*- coding: utf-8 -*-

# Copyright © 2013-2015 Udo Spallek, Roberto Alsina and others.

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
from __future__ import unicode_literals

import os
import uuid
import natsort

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from nikola import utils
from nikola.plugin_categories import RestExtension

# WARNING: the directive name is post-list
#          (with a DASH instead of an UNDERSCORE)


class Plugin(RestExtension):
    name = "rest_post_list"

    def set_site(self, site):
        self.site = site
        directives.register_directive('post-list', PostList)
        PostList.site = site
        return super(Plugin, self).set_site(site)


class PostList(Directive):
    """
    Post List
    =========
    :Directive Arguments: None.
    :Directive Options: lang, start, stop, reverse, sort, tags, template, id
    :Directive Content: None.

    Provides a reStructuredText directive to create a list of posts.
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

    ``sort``: string
        Sort post list by one of each post's attributes, usually ``title`` or a
        custom ``priority``.  Defaults to None (chronological sorting).

    ``tags`` : string [, string...]
        Filter posts to show only posts having at least one of the ``tags``.
        Defaults to None.

    ``slugs`` : string [, string...]
        Filter posts to show only posts having at least one of the ``slugs``.
        Defaults to None.

    ``all`` : flag
        Shows all posts and pages in the post list.
        Defaults to show only posts with set *use_in_feeds*.

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
        'slugs': directives.unchanged,
        'all': directives.flag,
        'lang': directives.unchanged,
        'template': directives.path,
        'id': directives.unchanged,
    }

    def run(self):
        start = self.options.get('start')
        stop = self.options.get('stop')
        reverse = self.options.get('reverse', False)
        tags = self.options.get('tags')
        tags = [t.strip().lower() for t in tags.split(',')] if tags else []
        slugs = self.options.get('slugs')
        slugs = [s.strip() for s in slugs.split(',')] if slugs else []
        show_all = self.options.get('all', False)
        lang = self.options.get('lang', utils.LocaleBorg().current_lang)
        template = self.options.get('template', 'post_list_directive.tmpl')
        sort = self.options.get('sort')
        if self.site.invariant:  # for testing purposes
            post_list_id = self.options.get('id', 'post_list_' + 'fixedvaluethatisnotauuid')
        else:
            post_list_id = self.options.get('id', 'post_list_' + uuid.uuid4().hex)

        filtered_timeline = []
        posts = []
        step = -1 if reverse is None else None
        if show_all is None:
            timeline = [p for p in self.site.timeline]
        else:
            timeline = [p for p in self.site.timeline if p.use_in_feeds]

        for post in timeline:
            if tags:
                cont = True
                tags_lower = [t.lower() for t in post.tags]
                for tag in tags:
                    if tag in tags_lower:
                        cont = False

                if cont:
                    continue

            filtered_timeline.append(post)

        if sort:
            filtered_timeline = natsort.natsorted(filtered_timeline, key=lambda post: post.meta[lang][sort], alg=natsort.ns.F | natsort.ns.IC)

        for post in filtered_timeline[start:stop:step]:
            if slugs:
                cont = True
                for slug in slugs:
                    if slug == post.meta('slug'):
                        cont = False

                if cont:
                    continue

            bp = post.translated_base_path(lang)
            if os.path.exists(bp):
                self.state.document.settings.record_dependencies.add(bp)

            posts += [post]

        if not posts:
            return []
        self.state.document.settings.record_dependencies.add("####MAGIC####TIMELINE")

        template_data = {
            'lang': lang,
            'posts': posts,
            'date_format': self.site.GLOBAL_CONTEXT.get('date_format'),
            'post_list_id': post_list_id,
        }
        output = self.site.template_system.render_template(
            template, None, template_data)
        return [nodes.raw('', output, format='html')]
