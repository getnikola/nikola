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

"""Render the blog's main index."""

from __future__ import unicode_literals

from nikola.plugin_categories import Taxonomy


class Indexes(Taxonomy):
    """Classify for the blog's main index."""

    name = "classify_indexes"

    classification_name = "index"
    overview_page_variable_name = None
    more_than_one_classifications_per_post = False
    has_hierarchy = False
    show_list_as_index = True
    template_for_single_list = "index.tmpl"
    template_for_classification_overview = None
    apply_to_posts = True
    apply_to_pages = False
    omit_empty_classifications = False
    also_create_classifications_from_other_languages = False
    path_handler_docstrings = {
        'index_index': False,
        'index': """Link to a numbered index.

Example:

link://index/3 => /index-3.html""",
        'index_atom': """Link to a numbered Atom index.

Example:

link://index_atom/3 => /index-3.atom""",
        'index_rss': """A link to the RSS feed path.

Example:

link://rss => /blog/rss.xml""",
    }

    def set_site(self, site):
        """Set Nikola site."""
        # Redirect automatically generated 'index_rss' path handler to 'rss' for compatibility with old rss plugin
        site.register_path_handler('rss', lambda name, lang: site.path_handlers['index_rss'](name, lang))
        site.path_handlers['rss'].__doc__ = """A link to the RSS feed path.

Example:

    link://rss => /blog/rss.xml
        """.strip()
        return super(Indexes, self).set_site(site)

    def get_implicit_classifications(self, lang):
        """Return a list of classification strings which should always appear in posts_per_classification."""
        return [""]

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        return [""]

    def get_classification_friendly_name(self, classification, lang, only_last_component=False):
        """Extract a friendly name from the classification."""
        return self.site.config["BLOG_TITLE"](lang)

    def get_path(self, classification, lang, dest_type='page'):
        """Return a path for the given classification."""
        if dest_type == 'rss':
            return [self.site.config['RSS_PATH'](lang)], True
        # 'page' (index) or 'feed' (Atom)
        page_number = None
        if dest_type == 'page':
            # Interpret argument as page number
            try:
                page_number = int(classification)
            except:
                pass
        return [self.site.config['INDEX_PATH'](lang)], 'always', page_number

    def provide_context_and_uptodate(self, classification, lang, node=None):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        kw = {
        }
        context = {
            "title": self.site.config["INDEXES_TITLE"](lang) or self.site.config["BLOG_TITLE"](lang),
            "description": self.site.config["BLOG_DESCRIPTION"](lang),
            "pagekind": ["main_index", "index"],
        }
        kw.update(context)
        return context, kw

    def should_generate_classification_page(self, classification, post_list, lang):
        """Only generates list of posts for classification if this function returns True."""
        return not self.site.config["DISABLE_INDEXES_PLUGIN_INDEX_AND_ATOM_FEED"]

    def should_generate_rss_for_classification_page(self, classification, post_list, lang):
        """Only generates RSS feed for list of posts for classification if this function returns True."""
        return not self.site.config["DISABLE_INDEXES_PLUGIN_RSS_FEED"]
