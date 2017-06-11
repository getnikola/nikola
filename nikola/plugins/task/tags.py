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

"""Render the tag pages and feeds."""

from __future__ import unicode_literals

from nikola.plugin_categories import Taxonomy
from nikola import utils


class ClassifyTags(Taxonomy):
    """Classify the posts by tags."""

    name = "classify_tags"

    classification_name = "tag"
    overview_page_variable_name = "tags"
    overview_page_items_variable_name = "items"
    more_than_one_classifications_per_post = True
    has_hierarchy = False
    show_list_as_subcategories_list = False
    generate_atom_feeds_for_post_lists = True
    template_for_classification_overview = "tags.tmpl"
    always_disable_rss = False
    apply_to_posts = True
    apply_to_pages = False
    omit_empty_classifications = True
    also_create_classifications_from_other_languages = True
    add_other_languages_variable = True
    path_handler_docstrings = {
        'tag_index': """A link to the tag index.

Example:

link://tag_index => /tags/index.html""",
        'tag': """A link to a tag's page. Takes page number as optional keyword argument.

Example:

link://tag/cats => /tags/cats.html""",
        'tag_atom': """A link to a tag's Atom feed.

Example:

link://tag_atom/cats => /tags/cats.atom""",
        'tag_rss': """A link to a tag's RSS feed.

Example:

link://tag_rss/cats => /tags/cats.xml""",
    }

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        super(ClassifyTags, self).set_site(site)
        self.show_list_as_index = self.site.config['TAG_PAGES_ARE_INDEXES']
        self.template_for_single_list = "tagindex.tmpl" if self.show_list_as_index else "tag.tmpl"
        self.minimum_post_count_per_classification_in_overview = self.site.config['TAGLIST_MINIMUM_POSTS']
        self.translation_manager = utils.ClassificationTranslationManager()

    def is_enabled(self, lang=None):
        """Return True if this taxonomy is enabled, or False otherwise."""
        return True

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        return post.tags_for_language(lang)

    def get_classification_friendly_name(self, classification, lang, only_last_component=False):
        """Extract a friendly name from the classification."""
        return classification

    def slugify_tag_name(self, name, lang):
        """Slugify a tag name."""
        if lang is None:  # TODO: remove in v8
            utils.LOGGER.warn("ClassifyTags.slugify_tag_name() called without language!")
            lang = ''
        if self.site.config['SLUG_TAG_PATH']:
            name = utils.slugify(name, lang)
        return name

    def get_overview_path(self, lang, dest_type='page'):
        """Return a path for the list of all classifications."""
        if self.site.config['TAGS_INDEX_PATH'](lang):
            path = self.site.config['TAGS_INDEX_PATH'](lang)
            if path.endswith('/index'):  # TODO: remove in v8
                utils.LOGGER.warn("TAGS_INDEX_PATH for language {0} is missing a .html extension. Please update your configuration!".format(lang))
                path += '.html'
            return [_f for _f in [path] if _f], 'never'
        else:
            return [_f for _f in [self.site.config['TAG_PATH'](lang)] if _f], 'always'

    def get_path(self, classification, lang, dest_type='page'):
        """Return a path for the given classification."""
        return [_f for _f in [
            self.site.config['TAG_PATH'](lang),
            self.slugify_tag_name(classification, lang)] if _f], 'auto'

    def provide_overview_context_and_uptodate(self, lang):
        """Provide data for the context and the uptodate list for the list of all classifiations."""
        kw = {
            "tag_path": self.site.config['TAG_PATH'],
            "tag_pages_are_indexes": self.site.config['TAG_PAGES_ARE_INDEXES'],
            "taglist_minimum_post_count": self.site.config['TAGLIST_MINIMUM_POSTS'],
            "tzinfo": self.site.tzinfo,
            "tag_pages_descriptions": self.site.config['TAG_PAGES_DESCRIPTIONS'],
            "tag_pages_titles": self.site.config['TAG_PAGES_TITLES'],
        }
        context = {
            "title": self.site.MESSAGES[lang]["Tags"],
            "description": self.site.MESSAGES[lang]["Tags"],
            "pagekind": ["list", "tags_page"],
        }
        kw.update(context)
        return context, kw

    def provide_context_and_uptodate(self, classification, lang, node=None):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        kw = {
            "tag_path": self.site.config['TAG_PATH'],
            "tag_pages_are_indexes": self.site.config['TAG_PAGES_ARE_INDEXES'],
            "taglist_minimum_post_count": self.site.config['TAGLIST_MINIMUM_POSTS'],
            "tzinfo": self.site.tzinfo,
            "tag_pages_descriptions": self.site.config['TAG_PAGES_DESCRIPTIONS'],
            "tag_pages_titles": self.site.config['TAG_PAGES_TITLES'],
        }
        context = {
            "title": self.site.config['TAG_PAGES_TITLES'].get(lang, {}).get(classification, self.site.MESSAGES[lang]["Posts about %s"] % classification),
            "description": self.site.config['TAG_PAGES_DESCRIPTIONS'].get(lang, {}).get(classification),
            "pagekind": ["tag_page", "index" if self.show_list_as_index else "list"],
            "tag": classification,
        }
        if self.show_list_as_index:
            context["rss_link"] = """<link rel="alternate" type="application/rss+xml" type="application/rss+xml" title="RSS for tag {0} ({1})" href="{2}">""".format(classification, lang, self.site.link("tag_rss", classification, lang))
        kw.update(context)
        return context, kw

    def get_other_language_variants(self, classification, lang, classifications_per_language):
        """Return a list of variants of the same tag in other languages."""
        return self.translation_manager.get_translations_as_list(classification, lang, classifications_per_language)

    def postprocess_posts_per_classification(self, posts_per_classification_per_language, flat_hierarchy_per_lang=None, hierarchy_lookup_per_lang=None):
        """Rearrange, modify or otherwise use the list of posts per classification and per language."""
        self.translation_manager.read_from_config(self.site, 'TAG', posts_per_classification_per_language, False)
