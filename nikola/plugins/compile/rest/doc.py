# -*- coding: utf-8 -*-

# Copyright © 2012-2025 Roberto Alsina and others.

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

from nikola.utils import split_explicit_title, LOGGER, slugify
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
        return super().set_site(site)


def _find_post(slug):
    """Find a post with the given slug in posts or pages."""
    twin_slugs = False
    post = None
    for p in doc_role.site.timeline:
        if p.meta('slug') == slug:
            if post is None:
                post = p
            else:
                twin_slugs = True
                break
    return post, twin_slugs


def _doc_link(rawtext, text, options={}, content=[]):
    """Handle the doc role."""
    # split link's text and post's slug in role content
    has_explicit_title, title, slug = split_explicit_title(text)
    if '#' in slug:
        slug, fragment = slug.split('#', 1)
    else:
        fragment = None

    # Look for the unslugified input first, then try to slugify (Issue #3450)
    post, twin_slugs = _find_post(slug)
    if post is None:
        slug = slugify(slug)
        post, twin_slugs = _find_post(slug)

    try:
        if post is None:
            raise ValueError("No post with matching slug found.")
    except ValueError:
        return False, False, None, None, slug

    if not has_explicit_title:
        # use post's title as link's text
        title = post.title()
    permalink = post.permalink()
    if fragment:
        permalink += '#' + fragment

    return True, twin_slugs, title, permalink, slug


def doc_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Handle the doc role."""
    success, twin_slugs, title, permalink, slug = _doc_link(rawtext, text, options, content)
    if success:
        if twin_slugs:
            inliner.reporter.warning(
                f'More than one post with the same slug. Using "{permalink}"')
            LOGGER.warning(
                f'More than one post with the same slug. Using "{permalink}" for doc role')
        node = make_link_node(rawtext, title, permalink, options)
        return [node], []
    else:
        msg = inliner.reporter.error(
            f'"{slug}" slug doesn\'t exist.',
            line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]


def doc_shortcode(*args, **kwargs):
    """Implement the doc shortcode."""
    text = kwargs['data']
    success, twin_slugs, title, permalink, slug = _doc_link(text, text, LOGGER)
    if success:
        if twin_slugs:
            LOGGER.warning(
                f'More than one post with the same slug. Using "{permalink}" for doc shortcode')
        return f'<a href="{permalink}">{title}</a>'
    else:
        LOGGER.error(
            f'"{slug}" slug doesn\'t exist.')
        return f'<span class="error text-error" style="color: red;">Invalid link: {text}</span>'


def make_link_node(rawtext, text, url, options):
    """Make a reST link node."""
    node = nodes.reference(rawtext, text, refuri=url, *options)
    return node
