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

"""Render the category pages and feeds."""

import os

from nikola.plugin_categories import Taxonomy
from nikola import utils, hierarchy_utils


class ClassifyCategories(Taxonomy):
    """Classify the posts by categories."""

    name = "classify_categories"

    classification_name = "category"
    overview_page_variable_name = "categories"
    overview_page_items_variable_name = "cat_items"
    overview_page_hierarchy_variable_name = "cat_hierarchy"
    more_than_one_classifications_per_post = False
    has_hierarchy = True
    include_posts_from_subhierarchies = True
    include_posts_into_hierarchy_root = False
    show_list_as_subcategories_list = False
    template_for_classification_overview = "tags.tmpl"
    always_disable_rss = False
    always_disable_atom = False
    apply_to_posts = True
    apply_to_pages = False
    minimum_post_count_per_classification_in_overview = 1
    omit_empty_classifications = True
    add_other_languages_variable = True
    path_handler_docstrings = {
        'category_index': """A link to the category index.

Example:

link://category_index => /categories/index.html""",
        'category': """A link to a category. Takes page number as optional keyword argument.

Example:

link://category/dogs => /categories/dogs.html""",
        'category_atom': """A link to a category's Atom feed.

Example:

link://category_atom/dogs => /categories/dogs.atom""",
        'category_rss': """A link to a category's RSS feed.

Example:

link://category_rss/dogs => /categories/dogs.xml""",
    }

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        super().set_site(site)
        self.show_list_as_index = self.site.config['CATEGORY_PAGES_ARE_INDEXES']
        self.template_for_single_list = "tagindex.tmpl" if self.show_list_as_index else "tag.tmpl"
        self.translation_manager = utils.ClassificationTranslationManager()

        # Needed to undo names for CATEGORY_PAGES_FOLLOW_DESTPATH
        self.destpath_names_reverse = {}
        for lang in self.site.config['TRANSLATIONS']:
            self.destpath_names_reverse[lang] = {}
            for k, v in self.site.config['CATEGORY_DESTPATH_NAMES'](lang).items():
                self.destpath_names_reverse[lang][v] = k
        self.destpath_names_reverse = utils.TranslatableSetting(
            '_CATEGORY_DESTPATH_NAMES_REVERSE', self.destpath_names_reverse,
            self.site.config['TRANSLATIONS'])

    def is_enabled(self, lang=None):
        """Return True if this taxonomy is enabled, or False otherwise."""
        return True

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        cat = post.meta('category', lang=lang).strip()
        return [cat] if cat else []

    def get_classification_friendly_name(self, classification, lang, only_last_component=False):
        """Extract a friendly name from the classification."""
        classification = self.extract_hierarchy(classification)
        return classification[-1] if classification else ''

    def get_overview_path(self, lang, dest_type='page'):
        """Return a path for the list of all classifications."""
        if self.site.config['CATEGORIES_INDEX_PATH'](lang):
            path = self.site.config['CATEGORIES_INDEX_PATH'](lang)
            append_index = 'never'
        else:
            path = self.site.config['CATEGORY_PATH'](lang)
            append_index = 'always'
        return [component for component in path.split('/') if component], append_index

    def slugify_tag_name(self, name, lang):
        """Slugify a tag name."""
        if self.site.config['SLUG_TAG_PATH']:
            name = utils.slugify(name, lang)
        return name

    def slugify_category_name(self, path, lang):
        """Slugify a category name."""
        if self.site.config['CATEGORY_OUTPUT_FLAT_HIERARCHY']:
            path = path[-1:]  # only the leaf
        result = [self.slugify_tag_name(part, lang) for part in path]
        result[0] = self.site.config['CATEGORY_PREFIX'] + result[0]
        if not self.site.config['PRETTY_URLS']:
            result = ['-'.join(result)]
        return result

    def get_path(self, classification, lang, dest_type='page'):
        """Return a path for the given classification."""
        cat_string = '/'.join(classification)
        classification_raw = classification  # needed to undo CATEGORY_DESTPATH_NAMES
        destpath_names_reverse = self.destpath_names_reverse(lang)
        if self.site.config['CATEGORY_PAGES_FOLLOW_DESTPATH']:
            base_dir = None
            for post in self.site.posts_per_category[cat_string]:
                if post.category_from_destpath:
                    base_dir = post.folder_base(lang)
                    # Handle CATEGORY_DESTPATH_NAMES
                    if cat_string in destpath_names_reverse:
                        cat_string = destpath_names_reverse[cat_string]
                        classification_raw = cat_string.split('/')
                    break

            if not self.site.config['CATEGORY_DESTPATH_TRIM_PREFIX']:
                # If prefixes are not trimmed, we'll already have the base_dir in classification_raw
                base_dir = ''

            if base_dir is None:
                # fallback: first POSTS entry + classification
                base_dir = self.site.config['POSTS'][0][1]
            base_dir_list = base_dir.split(os.sep)
            sub_dir = [self.slugify_tag_name(part, lang) for part in classification_raw]
            return [_f for _f in (base_dir_list + sub_dir) if _f], 'auto'
        else:
            return [_f for _f in [self.site.config['CATEGORY_PATH'](lang)] if _f] + self.slugify_category_name(
                classification, lang), 'auto'

    def extract_hierarchy(self, classification):
        """Given a classification, return a list of parts in the hierarchy."""
        return hierarchy_utils.parse_escaped_hierarchical_category_name(classification)

    def recombine_classification_from_hierarchy(self, hierarchy):
        """Given a list of parts in the hierarchy, return the classification string."""
        return hierarchy_utils.join_hierarchical_category_path(hierarchy)

    def provide_overview_context_and_uptodate(self, lang):
        """Provide data for the context and the uptodate list for the list of all classifiations."""
        kw = {
            'category_path': self.site.config['CATEGORY_PATH'],
            'category_prefix': self.site.config['CATEGORY_PREFIX'],
            "category_pages_are_indexes": self.site.config['CATEGORY_PAGES_ARE_INDEXES'],
            "tzinfo": self.site.tzinfo,
            "category_descriptions": self.site.config['CATEGORY_DESCRIPTIONS'],
            "category_titles": self.site.config['CATEGORY_TITLES'],
        }
        context = {
            "title": self.site.MESSAGES[lang]["Categories"],
            "description": self.site.MESSAGES[lang]["Categories"],
            "pagekind": ["list", "tags_page"],
            "category_descriptions": self.site.config['CATEGORY_DESCRIPTIONS'](lang),
            "category_titles": self.site.config['CATEGORY_TITLES'](lang),
        }
        kw.update(context)
        return context, kw

    def provide_context_and_uptodate(self, classification, lang, node=None):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        cat_path = self.extract_hierarchy(classification)
        kw = {
            'category_path': self.site.config['CATEGORY_PATH'],
            'category_prefix': self.site.config['CATEGORY_PREFIX'],
            "category_pages_are_indexes": self.site.config['CATEGORY_PAGES_ARE_INDEXES'],
            "tzinfo": self.site.tzinfo,
            "category_descriptions": self.site.config['CATEGORY_DESCRIPTIONS'],
            "category_titles": self.site.config['CATEGORY_TITLES'],
        }
        posts = self.site.posts_per_classification[self.classification_name][lang]
        if node is None:
            children = []
        else:
            children = [child for child in node.children if len([post for post in posts.get(child.classification_name, []) if self.site.config['SHOW_UNTRANSLATED_POSTS'] or post.is_translation_available(lang)]) > 0]
        subcats = [(child.name, self.site.link(self.classification_name, child.classification_name, lang)) for child in children]
        friendly_name = self.get_classification_friendly_name(classification, lang)
        context = {
            "title": self.site.config['CATEGORY_TITLES'](lang).get(classification, self.site.MESSAGES[lang]["Posts about %s"] % friendly_name),
            "description": self.site.config['CATEGORY_DESCRIPTIONS'](lang).get(classification),
            "pagekind": ["tag_page", "index" if self.show_list_as_index else "list"],
            "tag": friendly_name,
            "category": classification,
            "category_path": cat_path,
            "subcategories": subcats,
        }
        kw.update(context)
        return context, kw

    def get_other_language_variants(self, classification, lang, classifications_per_language):
        """Return a list of variants of the same category in other languages."""
        return self.translation_manager.get_translations_as_list(classification, lang, classifications_per_language)

    def postprocess_posts_per_classification(self, posts_per_classification_per_language, flat_hierarchy_per_lang=None, hierarchy_lookup_per_lang=None):
        """Rearrange, modify or otherwise use the list of posts per classification and per language."""
        self.translation_manager.read_from_config(self.site, 'CATEGORY', posts_per_classification_per_language, False)

    def should_generate_classification_page(self, classification, post_list, lang):
        """Only generates list of posts for classification if this function returns True."""
        if self.site.config["CATEGORY_PAGES_FOLLOW_DESTPATH"]:
            # In destpath mode, allow users to replace the default category index with a custom page.
            classification_hierarchy = self.extract_hierarchy(classification)
            dest_list, _ = self.get_path(classification_hierarchy, lang)
            short_destination = os.sep.join(dest_list + [self.site.config["INDEX_FILE"]])
            if short_destination in self.site.post_per_file:
                return False
        return True

    def should_generate_atom_for_classification_page(self, classification, post_list, lang):
        """Only generates Atom feed for list of posts for classification if this function returns True."""
        return True

    def should_generate_rss_for_classification_page(self, classification, post_list, lang):
        """Only generates RSS feed for list of posts for classification if this function returns True."""
        return True
