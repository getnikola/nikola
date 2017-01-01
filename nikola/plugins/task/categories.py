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

"""Render the category pages and feeds."""

from __future__ import unicode_literals

from nikola.plugin_categories import Taxonomy
from nikola import utils


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
    generate_atom_feeds_for_post_lists = True
    template_for_classification_overview = "tags.tmpl"
    always_disable_rss = False
    apply_to_posts = True
    apply_to_pages = False
    minimum_post_count_per_classification_in_overview = 1
    omit_empty_classifications = True
    also_create_classifications_from_other_languages = True

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        super(ClassifyCategories, self).set_site(site)
        self.show_list_as_index = self.site.config['CATEGORY_PAGES_ARE_INDEXES']
        self.template_for_single_list = "tagindex.tmpl" if self.show_list_as_index else "tag.tmpl"

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
        """A path handler for the list of all classifications."""
        if self.site.config['CATEGORIES_INDEX_PATH'](lang):
            return [_f for _f in [self.site.config['CATEGORIES_INDEX_PATH'](lang)] if _f], 'never'
        else:
            return [_f for _f in [self.site.config['CATEGORY_PATH'](lang)] if _f], 'always'

    def slugify_tag_name(self, name, lang):
        """Slugify a tag name."""
        if self.site.config['SLUG_TAG_PATH']:
            name = utils.slugify(name, lang)
        return name

    def slugify_category_name(self, path, lang):
        """Slugify a category name."""
        if lang is None:  # TODO: remove in v8
            utils.LOGGER.warn("ClassifyCategories.slugify_category_name() called without language!")
            lang = ''
        if self.site.config['CATEGORY_OUTPUT_FLAT_HIERARCHY']:
            path = path[-1:]  # only the leaf
        result = [self.slugify_tag_name(part, lang) for part in path]
        result[0] = self.site.config['CATEGORY_PREFIX'] + result[0]
        if not self.site.config['PRETTY_URLS']:
            result = ['-'.join(result)]
        return result

    def get_path(self, classification, lang, dest_type='page'):
        """A path handler for the given classification."""
        return [_f for _f in [self.site.config['CATEGORY_PATH'](lang)] if _f] + self.slugify_category_name(classification, lang), 'auto'

    def extract_hierarchy(self, classification):
        """Given a classification, return a list of parts in the hierarchy."""
        return utils.parse_escaped_hierarchical_category_name(classification)

    def recombine_classification_from_hierarchy(self, hierarchy):
        """Given a list of parts in the hierarchy, return the classification string."""
        return utils.join_hierarchical_category_path(hierarchy)

    def provide_overview_context_and_uptodate(self, lang):
        """Provide data for the context and the uptodate list for the list of all classifiations."""
        kw = {
            'category_path': self.site.config['CATEGORY_PATH'],
            'category_prefix': self.site.config['CATEGORY_PREFIX'],
            "category_pages_are_indexes": self.site.config['CATEGORY_PAGES_ARE_INDEXES'],
            "tzinfo": self.site.tzinfo,
            "category_pages_descriptions": self.site.config['CATEGORY_PAGES_DESCRIPTIONS'],
            "category_pages_titles": self.site.config['CATEGORY_PAGES_TITLES'],
        }
        context = {
            "title": self.site.MESSAGES[lang]["Categories"],
            "description": self.site.MESSAGES[lang]["Categories"],
            "pagekind": ["list", "tags_page"],
        }
        kw.update(context)
        return context, kw

    def provide_context_and_uptodate(self, cat, lang, node=None):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        cat_path = self.extract_hierarchy(cat)
        kw = {
            'category_path': self.site.config['CATEGORY_PATH'],
            'category_prefix': self.site.config['CATEGORY_PREFIX'],
            "category_pages_are_indexes": self.site.config['CATEGORY_PAGES_ARE_INDEXES'],
            "tzinfo": self.site.tzinfo,
            "category_pages_descriptions": self.site.config['CATEGORY_PAGES_DESCRIPTIONS'],
            "category_pages_titles": self.site.config['CATEGORY_PAGES_TITLES'],
        }
        posts = self.site.posts_per_classification[self.classification_name][lang]
        children = [child for child in node.children if len([post for post in posts.get(child.classification_name, []) if self.site.config['SHOW_UNTRANSLATED_POSTS'] or post.is_translation_available(lang)]) > 0]
        subcats = [(child.name, self.site.link(self.classification_name, child.classification_name, lang), child.classification_name, child.classification_path) for child in children]
        friendly_name = self.get_classification_friendly_name(cat, lang)
        context = {
            "title": self.site.config['CATEGORY_PAGES_TITLES'].get(lang, {}).get(cat, self.site.MESSAGES[lang]["Posts about %s"] % friendly_name),
            "description": self.site.config['CATEGORY_PAGES_DESCRIPTIONS'].get(lang, {}).get(cat),
            "kind": "category",
            "pagekind": ["tag_page", "index" if self.show_list_as_index else "list"],
            "tag": friendly_name,
            "category": cat,
            "category_path": cat_path,
            "subcategories": subcats,
        }
        if self.show_list_as_index:
            context["rss_link"] = """<link rel="alternate" type="application/rss+xml" type="application/rss+xml" title="RSS for tag {0} ({1})" href="{2}">""".format(friendly_name, lang, self.site.link("category_rss", cat, lang))
        kw.update(context)
        return context, kw
