# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Classify the posts in archives."""

import os
import nikola.utils
import datetime
from nikola.plugin_categories import Taxonomy


class Archive(Taxonomy):
    """Classify the post archives."""

    name = "classify_archive"

    classification_name = "archive"
    metadata_name = None
    overview_page_variable_name = "archive"
    more_than_one_classifications_per_post = False
    has_hierarchy = True
    include_posts_from_subhierarchies = True
    include_posts_into_hierarchy_root = True
    generate_atom_feeds_for_post_lists = False
    template_for_classification_overview = None
    always_disable_rss = True
    apply_to_posts = True
    apply_to_pages = False
    minimum_post_count_per_classification_in_overview = 1
    omit_empty_classifications = False
    also_create_classifications_from_other_languages = False

    def set_site(self, site):
        """Set Nikola site."""
        # Sanity checks
        if (site.config['CREATE_MONTHLY_ARCHIVE'] and site.config['CREATE_SINGLE_ARCHIVE']) and not site.config['CREATE_FULL_ARCHIVES']:
            raise Exception('Cannot create monthly and single archives at the same time.')
        # Finish setup
        self.show_list_as_subcategories_list = False if site.config['CREATE_FULL_ARCHIVES'] else "list.tmpl"
        self.show_list_as_index = site.config['ARCHIVES_ARE_INDEXES']
        self.template_for_list_of_one_classification = "archiveindex.tmpl" if site.config['ARCHIVES_ARE_INDEXES'] else "list_post.tmpl"
        # Determine maximal hierarchy height
        if site.config['CREATE_DAILY_ARCHIVE'] or site.config['CREATE_FULL_ARCHIVES']:
            self.max_levels = 3
        elif site.config['CREATE_MONTHLY_ARCHIVE']:
            self.max_levels = 2
        elif site.config['CREATE_SINGLE_ARCHIVE']:
            self.max_levels = 0
        else:
            self.max_levels = 1
        return super(Archive, self).set_site(site)

    def is_enabled(self, lang=None):
        """Return True if this taxonomy is enabled, or False otherwise."""
        return True

    def get_implicit_classifications(self, lang):
        """Return a list of classification strings which should always appear in posts_per_classification."""
        return ['']

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        levels = ['{year:04d}', '{month:02d}', '{day:02d}'][:self.max_levels]
        levels = [level.format(year=post.date.year, month=post.date.month, day=post.date.day) for level in levels]
        return ['/'.join(levels)]

    def sort_classifications(self, classifications, lang, level=None):
        """Sort the given list of classification strings."""
        if level in (0, 1):
            # Years or months: sort descending
            classifications.sort()
            classifications.reverse()

    def get_classification_printable_name(self, classification, lang, only_last_component=False):
        """Extract a printable name from the classification."""
        if len(classification) == 0:
            return ""
        elif len(classification) == 1:
            return classification[0]
        elif len(classification) == 2:
            nikola.utils.LocaleBorg().get_month_name(int(classification[1]), lang)
        else:
            # Fallback
            return '/'.join(classification)

    def get_path(self, classification, lang, type='page'):
        """A path handler for the given classification."""
        components = [self.site.config['ARCHIVE_PATH']]
        if classification:
            components.extend(classification)
            add_index = 'always'
        else:
            components.append(os.path.splitext(self.site.config['ARCHIVE_FILENAME'])[0])
            add_index = 'never'
        return [_f for _f in components if _f], add_index

    def extract_hierarchy(self, classification):
        """Given a classification, return a list of parts in the hierarchy."""
        return classification.split('/') if classification else []

    def recombine_classification_from_hierarchy(self, hierarchy):
        """Given a list of parts in the hierarchy, return the classification string."""
        return '/'.join(hierarchy)

    def provide_context_and_uptodate(self, classification, lang):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        hierarchy = self.extract_hierarchy(classification)
        kw = {
            "messages": self.site.MESSAGES,
        }
        page_kind = "list"
        if self.show_list_as_index:
            if not self.show_list_as_subcategories_list or len(hierarchy) == self.max_levels:
                page_kind = "index"
        if len(hierarchy) == 0:
            title = kw["messages"][lang]["Archive"]
            kw["is_feed_stale"] = False
        elif len(hierarchy) == 1:
            title = kw["messages"][lang]["Posts for year %s"] % hierarchy[0]
            kw["is_feed_stale"] = (datetime.datetime.utcnow().strftime("%Y") != hierarchy[0])
        elif len(hierarchy) == 2:
            title = kw["messages"][lang]["Posts for {month} {year}"].format(
                year=hierarchy[0],
                month=nikola.utils.LocaleBorg().get_month_name(int(hierarchy[1]), lang))
            kw["is_feed_stale"] = (datetime.datetime.utcnow().strftime("%Y/%m") != classification)
        elif len(hierarchy) == 3:
            title = kw["messages"][lang]["Posts for {month} {day}, {year}"].format(
                year=hierarchy[0],
                month=nikola.utils.LocaleBorg().get_month_name(int(hierarchy[1]), lang),
                day=int(hierarchy[2]))
            kw["is_feed_stale"] = (datetime.datetime.utcnow().strftime("%Y/%m/%d") != classification)
        else:
            raise Exception("Cannot interpret classification {}!".format(repr(classification)))
        context = {
            "title": title,
            "classification_title": classification,
            "pagekind": [page_kind, "archive_page"],
        }
        if page_kind == 'index':
            context["archive_name"] = classification if classification else None
            context["is_feed_stale"] = kw["is_feed_stale"]
        kw.update(context)
        return context, kw

    def should_generate_classification_list(self, classification, post_list, lang):
        """Only generates list of posts for classification if this function returns True."""
        return classification == "" or len(post_list) > 0
