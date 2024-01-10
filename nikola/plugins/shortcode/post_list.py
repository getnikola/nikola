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

"""Post list shortcode."""


import operator
import os
import uuid

import natsort

from nikola import utils
from nikola.packages.datecond import date_in_range
from nikola.plugin_categories import ShortcodePlugin


class PostListShortcode(ShortcodePlugin):
    """Provide a shortcode to create a list of posts.

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
          * value: integer, 'now', 'today', or dateutil-compatible date input

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

    name = "post_list"

    def set_site(self, site):
        """Set the site."""
        super().set_site(site)
        site.register_shortcode('post-list', self.handler)

    def handler(self, start=None, stop=None, reverse=False, tags=None, require_all_tags=False, categories=None,
                sections=None, slugs=None, post_type='post', type=False,
                lang=None, template='post_list_directive.tmpl', sort=None,
                id=None, data=None, state=None, site=None, date=None, filename=None, post=None):
        """Generate HTML for post-list."""
        if lang is None:
            lang = utils.LocaleBorg().current_lang
        if site.invariant:  # for testing purposes
            post_list_id = id or 'post_list_' + 'fixedvaluethatisnotauuid'
        else:
            post_list_id = id or 'post_list_' + uuid.uuid4().hex

        # Get post from filename if available
        if filename:
            self_post = site.post_per_input_file.get(filename)
        else:
            self_post = None

        if self_post:
            self_post.register_depfile("####MAGIC####TIMELINE", lang=lang)
            self_post.register_depfile("####MAGIC####CONFIG:GLOBAL_CONTEXT", lang=lang)

        # If we get strings for start/stop, make them integers
        if start is not None:
            start = int(start)
        if stop is not None:
            stop = int(stop)

        # Parse tags/categories/sections/slugs (input is strings)
        categories = [c.strip().lower() for c in categories.split(',')] if categories else []
        sections = [s.strip().lower() for s in sections.split(',')] if sections else []
        slugs = [s.strip() for s in slugs.split(',')] if slugs else []

        filtered_timeline = []
        posts = []
        step = None if reverse is False else -1

        if type is not False:
            post_type = type

        if post_type == 'page' or post_type == 'pages':
            timeline = [p for p in site.timeline if not p.use_in_feeds]
        elif post_type == 'all':
            timeline = [p for p in site.timeline]
        else:  # post
            timeline = [p for p in site.timeline if p.use_in_feeds]

        # self_post should be removed from timeline because this is redundant
        timeline = [p for p in timeline if p.source_path != filename]

        if categories:
            timeline = [p for p in timeline if p.meta('category', lang=lang).lower() in categories]

        if sections:
            timeline = [p for p in timeline if p.section_name(lang).lower() in sections]

        if tags:
            tags = {t.strip().lower() for t in tags.split(',')}
            if require_all_tags:
                compare = set.issubset
            else:
                compare = operator.and_
            for post in timeline:
                post_tags = {t.lower() for t in post.tags}
                if compare(tags, post_tags):
                    filtered_timeline.append(post)
        else:
            filtered_timeline = timeline

        if sort:
            filtered_timeline = natsort.natsorted(filtered_timeline, key=lambda post: post.meta[lang][sort], alg=natsort.ns.F | natsort.ns.IC)

        if date:
            _now = utils.current_time()
            filtered_timeline = [p for p in filtered_timeline if date_in_range(utils.html_unescape(date), p.date, now=_now)]

        for post in filtered_timeline[start:stop:step]:
            if slugs:
                cont = True
                for slug in slugs:
                    if slug == post.meta('slug'):
                        cont = False

                if cont:
                    continue

            bp = post.translated_base_path(lang)
            if os.path.exists(bp) and state:
                state.document.settings.record_dependencies.add(bp)
            elif os.path.exists(bp) and self_post:
                self_post.register_depfile(bp, lang=lang)

            posts += [post]

        template_deps = site.template_system.template_deps(template, site.GLOBAL_CONTEXT)
        if state:
            # Register template as a dependency (Issue #2391)
            for d in template_deps:
                state.document.settings.record_dependencies.add(d)
        elif self_post:
            for d in template_deps:
                self_post.register_depfile(d, lang=lang)

        template_data = site.GLOBAL_CONTEXT.copy()
        template_data.update({
            'lang': lang,
            'posts': posts,
            # Need to provide str, not TranslatableSetting (Issue #2104)
            'date_format': site.GLOBAL_CONTEXT.get('date_format')[lang],
            'post_list_id': post_list_id,
            'messages': site.MESSAGES,
            '_link': site.link,
        })
        output = site.template_system.render_template(
            template, None, template_data)
        return output, template_deps


# Request file name from shortcode (Issue #2412)
PostListShortcode.handler.nikola_shortcode_pass_filename = True
