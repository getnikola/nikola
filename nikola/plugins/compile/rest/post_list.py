# -*- coding: utf-8 -*-

# Copyright © 2013 Udo Spallek, Roberto Alsina and others.

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
import sys

import uuid

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):
    name = "rest_post_list"

    def set_site(self, site):
        self.site = site
        directives.register_directive('post-list', PostList)
        PostList.site = site
        return super(Plugin, self).set_site(site)


class PostList(Directive):
    """ Restructured text extension to insert a list of posts.

    Usage:
    .. post_list:: [post_list_id]
        :lang: the language of the title and links (string)
        :slice-start: the start value of the slice of the post list (integer)
        :slice-stop: the stop value of the slice of the post list (integer)
        :slice-step: the step value of the slice of the post list (integer)
        :tags: shows only posts with tags (list of strings)
        :template: use an alternative template (uri string)

    The argument ``post_list_id`` sets an id for the post list.
    All arguments and options are optional.
    """
    required_arguments = 0
    optional_arguments = 1
    option_spec = {
        'lang': directives.unchanged,
        'slice-start': int,
        'slice-stop': int,
        'slice-step': int,
        'tags': directives.unchanged,
        'template': directives.uri,
    }

    def run(self):
        post_list_id = 'post_list_' + uuid.uuid4().hex
        if self.arguments:
            post_list_id = self.arguments[0]

        lang = self.options.get('lang', 'en')
        start = self.options.get('slice-start', None)
        stop = self.options.get('slice-stop', None)
        step = self.options.get('slice-step', None)
        tags = self.options.get('tags')
        tags = [t.strip().lower() for t in tags.split(',')]
        template = self.options.get('template', 'post_list_directive.tmpl')
        posts = []

        for post in self.site.timeline[start:stop:step]:
            if not post.use_in_feeds:
                continue

            cont = True
            for tag in tags:
                if tag in [t.lower() for t in post.tags]:
                    cont = False

            if cont:
                continue
            posts += [post]

        if not posts:
            return []

        template_data = {
            'lang': lang,
            'posts': posts,
            'date_format': self.site.GLOBAL_CONTEXT.get('date_format'),
            'post_list_id': post_list_id,
        }
        output = self.site.template_system.render_template(
            template, None, template_data)
        return [nodes.raw('', output, format='html')]
