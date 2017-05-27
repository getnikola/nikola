# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""reST role for linking to other documents."""

from docutils import nodes
from docutils.parsers.rst import roles

from nikola.utils import split_explicit_title, LOGGER
from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):
    """Plugin for doc role."""

    name = 'rest_doc'

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        roles.register_canonical_role('doc', doc_role)
        self.site.register_shortcode('doc', doc_shortcode)
        doc_role.site = site
        return super(Plugin, self).set_site(site)


def _doc_link(rawtext, text, options={}, content=[]):
    """Handle the doc role."""
    # split link's text and post's slug in role content
    has_explicit_title, title, slug = split_explicit_title(text)
    # check if the slug given is part of our blog posts/pages
    twin_slugs = False
    post = None
    for p in doc_role.site.timeline:
        if p.meta('slug') == slug:
            if post is None:
                post = p
            else:
                twin_slugs = True
                break

    try:
        if post is None:
            raise ValueError("No post with matching slug found.")
    except ValueError:
        return False, False, None, None, slug

    if not has_explicit_title:
        # use post's title as link's text
        title = post.title()
    permalink = post.permalink()

    return True, twin_slugs, title, permalink, slug


def doc_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Handle the doc role."""
    success, twin_slugs, title, permalink, slug = _doc_link(rawtext, text, options, content)
    if success:
        if twin_slugs:
            inliner.reporter.warning(
                'More than one post with the same slug. Using "{0}"'.format(permalink))
            LOGGER.warn(
                'More than one post with the same slug. Using "{0}" for doc role'.format(permalink))
        node = make_link_node(rawtext, title, permalink, options)
        return [node], []
    else:
        msg = inliner.reporter.error(
            '"{0}" slug doesn\'t exist.'.format(slug),
            line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]


def doc_shortcode(*args, **kwargs):
    """Implement the doc shortcode."""
    text = kwargs['data']
    success, twin_slugs, title, permalink, slug = _doc_link(text, text, LOGGER)
    if success:
        if twin_slugs:
            LOGGER.warn(
                'More than one post with the same slug. Using "{0}" for doc shortcode'.format(permalink))
        return '<a href="{0}">{1}</a>'.format(permalink, title)
    else:
        LOGGER.error(
            '"{0}" slug doesn\'t exist.'.format(slug))
        return '<span class="error text-error" style="color: red;">Invalid link: {0}</span>'.format(text)


def make_link_node(rawtext, text, url, options):
    """Make a reST link node."""
    node = nodes.reference(rawtext, text, refuri=url, *options)
    return node
