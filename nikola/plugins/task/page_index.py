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

"""Render the page index."""


from nikola.plugin_categories import Taxonomy


class PageIndex(Taxonomy):
    """Classify for the page index."""

    name = "classify_page_index"

    classification_name = "page_index_folder"
    overview_page_variable_name = "page_folder"
    more_than_one_classifications_per_post = False
    has_hierarchy = True
    include_posts_from_subhierarchies = False
    show_list_as_index = False
    template_for_single_list = "list.tmpl"
    template_for_classification_overview = None
    always_disable_rss = True
    always_disable_atom = True
    apply_to_posts = False
    apply_to_pages = True
    omit_empty_classifications = True
    path_handler_docstrings = {
        'page_index_folder_index': None,
        'page_index_folder': None,
        'page_index_folder_atom': None,
        'page_index_folder_rss': None,
    }

    def is_enabled(self, lang=None):
        """Return True if this taxonomy is enabled, or False otherwise."""
        return self.site.config["PAGE_INDEX"]

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        destpath = post.destination_path(lang, sep='/')
        if post.has_pretty_url(lang):
            idx = '/index.html'
            if destpath.endswith(idx):
                destpath = destpath[:-len(idx)]
        i = destpath.rfind('/')
        return [destpath[:i] if i >= 0 else '']

    def get_classification_friendly_name(self, dirname, lang, only_last_component=False):
        """Extract a friendly name from the classification."""
        return dirname

    def get_path(self, hierarchy, lang, dest_type='page'):
        """Return a path for the given classification."""
        return hierarchy, 'always'

    def extract_hierarchy(self, dirname):
        """Given a classification, return a list of parts in the hierarchy."""
        return dirname.split('/') if dirname else []

    def recombine_classification_from_hierarchy(self, hierarchy):
        """Given a list of parts in the hierarchy, return the classification string."""
        return '/'.join(hierarchy)

    def provide_context_and_uptodate(self, dirname, lang, node=None):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "filters": self.site.config['FILTERS'],
        }
        context = {
            "title": self.site.config['BLOG_TITLE'](lang),
            "pagekind": ["list", "front_page", "page_index"] if dirname == '' else ["list", "page_index"],
            "kind": "page_index_folder",
            "classification": dirname,
            "has_no_feeds": True,
        }
        kw.update(context)
        return context, kw

    def should_generate_classification_page(self, dirname, post_list, lang):
        """Only generates list of posts for classification if this function returns True."""
        short_destination = dirname + '/' + self.site.config['INDEX_FILE']
        for post in post_list:
            # If there is an index.html pending to be created from a page, do not generate the page index.
            if post.destination_path(lang, sep='/').lstrip('/') == short_destination.lstrip('/'):
                return False
        return True
