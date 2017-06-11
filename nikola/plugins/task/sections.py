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

"""Render the blog indexes."""

from __future__ import unicode_literals

from nikola.plugin_categories import Taxonomy
from nikola import utils


class ClassifySections(Taxonomy):
    """Classify the posts by sections."""

    name = "classify_sections"

    classification_name = "section_index"
    overview_page_variable_name = "sections"
    more_than_one_classifications_per_post = False
    has_hierarchy = False
    generate_atom_feeds_for_post_lists = False
    template_for_classification_overview = None
    apply_to_posts = True
    apply_to_pages = False
    omit_empty_classifications = True
    also_create_classifications_from_other_languages = False
    add_other_languages_variable = True
    path_handler_docstrings = {
        'section_index_index': False,
        'section_index': """Link to the index for a section.

Example:

link://section_index/cars => /cars/index.html""",
        'section_index_atom': """Link to the Atom index for a section.

Example:

link://section_index_atom/cars => /cars/index.atom""",
        'section_index_rss': """Link to the RSS feed for a section.

Example:

link://section_index_rss/cars => /cars/rss.xml""",
    }

    def set_site(self, site):
        """Set Nikola site."""
        super(ClassifySections, self).set_site(site)
        self.show_list_as_index = site.config["POSTS_SECTIONS_ARE_INDEXES"]
        self.template_for_single_list = "sectionindex.tmpl" if self.show_list_as_index else "list.tmpl"
        self.enable_for_lang = {}
        self.translation_manager = utils.ClassificationTranslationManager()

    def is_enabled(self, lang=None):
        """Return True if this taxonomy is enabled, or False otherwise."""
        if not self.site.config['POSTS_SECTIONS']:
            return False
        if lang is not None:
            return self.enable_for_lang.get(lang, False)
        return True

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        return [post.section_slug(lang)]

    def _get_section_name(self, section, lang):
        # Check whether we have a name for this section
        if section in self.site.config['POSTS_SECTION_NAME'](lang):
            return self.site.config['POSTS_SECTION_NAME'](lang)[section]
        else:
            return section.replace('-', ' ').title()

    def get_classification_friendly_name(self, section, lang, only_last_component=False):
        """Extract a friendly name from the classification."""
        return self._get_section_name(section, lang)

    def get_path(self, section, lang, dest_type='page'):
        """Return a path for the given classification."""
        result = [_f for _f in [self.site.config['SECTION_PATH'](lang), section] if _f]
        if dest_type == 'rss':
            return result + ['rss.xml'], 'never'
        return result, 'always'

    def provide_context_and_uptodate(self, classification, lang, node=None):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        kw = {
            "messages": self.site.MESSAGES,
        }
        section_name = self._get_section_name(classification, lang)
        # Compose section title
        section_title = section_name
        posts_section_title = self.site.config['POSTS_SECTION_TITLE'](lang)
        if isinstance(posts_section_title, dict):
            if classification in posts_section_title:
                section_title = posts_section_title[classification]
        elif isinstance(posts_section_title, (utils.bytes_str, utils.unicode_str)):
            section_title = posts_section_title
        section_title = section_title.format(name=section_name)
        # Compose context
        context = {
            "title": section_title,
            "description": self.site.config['POSTS_SECTION_DESCRIPTIONS'](lang)[classification] if classification in self.site.config['POSTS_SECTION_DESCRIPTIONS'](lang) else "",
            "pagekind": ["section_page", "index" if self.show_list_as_index else "list"],
            "section": classification,
        }
        kw.update(context)
        return context, kw

    def postprocess_posts_per_classification(self, posts_per_classification_per_language, flat_hierarchy_per_lang=None, hierarchy_lookup_per_lang=None):
        """Rearrange, modify or otherwise use the list of posts per classification and per language."""
        for lang, posts_per_section in posts_per_classification_per_language.items():
            # Don't build sections when there is only one, a.k.a. default setups
            sections = set()
            for section, posts in posts_per_section.items():
                for post in posts:
                    if not self.site.config["SHOW_UNTRANSLATED_POSTS"] and not post.is_translation_available(lang):
                        continue
                    sections.add(section)
            self.enable_for_lang[lang] = (len(sections) > 1)
        self.translation_manager.read_from_config(self.site, 'POSTS_SECTION', posts_per_classification_per_language, False)

    def should_generate_classification_page(self, classification, post_list, lang):
        """Only generates list of posts for classification if this function returns True."""
        short_destination = classification + '/' + self.site.config['INDEX_FILE']
        # If there is an index.html pending to be created from a page, do not generate the section page.
        # The section page would be useless anyways. (via Issue #2613)
        for post in self.site.timeline:
            if not self.site.config["SHOW_UNTRANSLATED_POSTS"] and not post.is_translation_available(lang):
                continue
            if post.destination_path(lang, sep='/') == short_destination:
                return False
        return True

    def get_other_language_variants(self, classification, lang, classifications_per_language):
        """Return a list of variants of the same section in other languages."""
        return self.translation_manager.get_translations_as_list(classification, lang, classifications_per_language)
