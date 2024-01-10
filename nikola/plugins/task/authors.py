# -*- coding: utf-8 -*-

# Copyright © 2015-2024 Juanjo Conti and others.

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

"""Render the author pages and feeds."""


from nikola.plugin_categories import Taxonomy
from nikola import utils


class ClassifyAuthors(Taxonomy):
    """Classify the posts by authors."""

    name = "classify_authors"

    classification_name = "author"
    overview_page_variable_name = "authors"
    more_than_one_classifications_per_post = False
    has_hierarchy = False
    template_for_classification_overview = "authors.tmpl"
    apply_to_posts = True
    apply_to_pages = False
    minimum_post_count_per_classification_in_overview = 1
    omit_empty_classifications = False
    add_other_languages_variable = True
    path_handler_docstrings = {
        'author_index': """ Link to the authors index.

        Example:

        link://authors/ => /authors/index.html""",
        'author': """Link to an author's page.

        Example:

        link://author/joe => /authors/joe.html""",
        'author_atom': """Link to an author's Atom feed.

Example:

link://author_atom/joe => /authors/joe.atom""",
        'author_rss': """Link to an author's RSS feed.

Example:

link://author_rss/joe => /authors/joe.xml""",
    }

    def set_site(self, site):
        """Set Nikola site."""
        super().set_site(site)
        self.show_list_as_index = site.config['AUTHOR_PAGES_ARE_INDEXES']
        self.more_than_one_classifications_per_post = site.config.get('MULTIPLE_AUTHORS_PER_POST', False)
        self.template_for_single_list = "authorindex.tmpl" if self.show_list_as_index else "author.tmpl"
        self.translation_manager = utils.ClassificationTranslationManager()

    def is_enabled(self, lang=None):
        """Return True if this taxonomy is enabled, or False otherwise."""
        if not self.site.config["ENABLE_AUTHOR_PAGES"]:
            return False
        if lang is not None:
            return self.generate_author_pages
        return True

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        if self.more_than_one_classifications_per_post:
            return post.authors(lang=lang)
        else:
            return [post.author(lang=lang)]

    def get_classification_friendly_name(self, classification, lang, only_last_component=False):
        """Extract a friendly name from the classification."""
        return classification

    def get_overview_path(self, lang, dest_type='page'):
        """Return a path for the list of all classifications."""
        path = self.site.config['AUTHOR_PATH'](lang)
        return [component for component in path.split('/') if component], 'always'

    def get_path(self, classification, lang, dest_type='page'):
        """Return a path for the given classification."""
        if self.site.config['SLUG_AUTHOR_PATH']:
            slug = utils.slugify(classification, lang)
        else:
            slug = classification
        return [self.site.config['AUTHOR_PATH'](lang), slug], 'auto'

    def provide_overview_context_and_uptodate(self, lang):
        """Provide data for the context and the uptodate list for the list of all classifiations."""
        kw = {
            "messages": self.site.MESSAGES,
        }
        context = {
            "title": kw["messages"][lang]["Authors"],
            "description": kw["messages"][lang]["Authors"],
            "permalink": self.site.link("author_index", None, lang),
            "pagekind": ["list", "authors_page"],
        }
        kw.update(context)
        return context, kw

    def provide_context_and_uptodate(self, classification, lang, node=None):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        descriptions = self.site.config['AUTHOR_PAGES_DESCRIPTIONS']
        kw = {
            "messages": self.site.MESSAGES,
        }
        context = {
            "author": classification,
            "title": kw["messages"][lang]["Posts by %s"] % classification,
            "description": descriptions[lang][classification] if lang in descriptions and classification in descriptions[lang] else None,
            "pagekind": ["index" if self.show_list_as_index else "list", "author_page"],
        }
        kw.update(context)
        return context, kw

    def get_other_language_variants(self, classification, lang, classifications_per_language):
        """Return a list of variants of the same author in other languages."""
        return self.translation_manager.get_translations_as_list(classification, lang, classifications_per_language)

    def postprocess_posts_per_classification(self, posts_per_classification_per_language, flat_hierarchy_per_lang=None, hierarchy_lookup_per_lang=None):
        """Rearrange, modify or otherwise use the list of posts per classification and per language."""
        more_than_one = False
        for lang, posts_per_author in posts_per_classification_per_language.items():
            authors = set()
            for author, posts in posts_per_author.items():
                for post in posts:
                    if not self.site.config["SHOW_UNTRANSLATED_POSTS"] and not post.is_translation_available(lang):
                        continue
                    authors.add(author)
            if len(authors) > 1:
                more_than_one = True
        self.generate_author_pages = self.site.config["ENABLE_AUTHOR_PAGES"] and more_than_one
        self.site.GLOBAL_CONTEXT["author_pages_generated"] = self.generate_author_pages
        self.translation_manager.add_defaults(posts_per_classification_per_language)
