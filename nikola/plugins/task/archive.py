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

"""Classify the posts in archives."""

import datetime
from collections import defaultdict

import natsort

import nikola.utils
from nikola.plugin_categories import Taxonomy


class Archive(Taxonomy):
    """Classify the post archives."""

    name = "classify_archive"

    classification_name = "archive"
    overview_page_variable_name = "archive"
    more_than_one_classifications_per_post = False
    has_hierarchy = True
    include_posts_from_subhierarchies = True
    include_posts_into_hierarchy_root = True
    subcategories_list_template = "list.tmpl"
    template_for_classification_overview = None
    always_disable_rss = True
    always_disable_atom = True
    apply_to_posts = True
    apply_to_pages = False
    minimum_post_count_per_classification_in_overview = 1
    omit_empty_classifications = False
    add_other_languages_variable = True
    path_handler_docstrings = {
        'archive_index': False,
        'archive': """Link to archive path, name is the year.

        Example:

        link://archive/2013 => /archives/2013/index.html""",
        'archive_atom': False,
        'archive_rss': False,
    }

    def set_site(self, site):
        """Set Nikola site."""
        # Sanity checks
        if (site.config['CREATE_MONTHLY_ARCHIVE'] and site.config['CREATE_SINGLE_ARCHIVE']) and not site.config['CREATE_FULL_ARCHIVES']:
            raise Exception('Cannot create monthly and single archives at the same time.')
        # Finish setup
        self.show_list_as_subcategories_list = not site.config['CREATE_FULL_ARCHIVES']
        self.show_list_as_index = site.config['ARCHIVES_ARE_INDEXES']
        self.template_for_single_list = "archiveindex.tmpl" if site.config['ARCHIVES_ARE_INDEXES'] else "archive.tmpl"
        # Determine maximum hierarchy height
        if site.config['CREATE_DAILY_ARCHIVE'] or site.config['CREATE_FULL_ARCHIVES']:
            self.max_levels = 3
        elif site.config['CREATE_MONTHLY_ARCHIVE']:
            self.max_levels = 2
        elif site.config['CREATE_SINGLE_ARCHIVE']:
            self.max_levels = 0
        else:
            self.max_levels = 1
        return super().set_site(site)

    def get_implicit_classifications(self, lang):
        """Return a list of classification strings which should always appear in posts_per_classification."""
        return ['']

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        levels = [str(post.date.year).zfill(4), str(post.date.month).zfill(2), str(post.date.day).zfill(2)]
        return ['/'.join(levels[:self.max_levels])]

    def sort_classifications(self, classifications, lang, level=None):
        """Sort the given list of classification strings."""
        if level in (0, 1):
            # Years or months: sort descending
            classifications.sort()
            classifications.reverse()

    def get_classification_friendly_name(self, classification, lang, only_last_component=False):
        """Extract a friendly name from the classification."""
        classification = self.extract_hierarchy(classification)
        if len(classification) == 0:
            return self.site.MESSAGES[lang]['Archive']
        elif len(classification) == 1:
            return classification[0]
        elif len(classification) == 2:
            if only_last_component:
                date_str = "{month}"
            else:
                date_str = "{month_year}"
            return nikola.utils.LocaleBorg().format_date_in_string(
                date_str,
                datetime.date(int(classification[0]), int(classification[1]), 1),
                lang)
        else:
            if only_last_component:
                return str(classification[2])
            return nikola.utils.LocaleBorg().format_date_in_string(
                "{month_day_year}",
                datetime.date(int(classification[0]), int(classification[1]), int(classification[2])),
                lang)

    def get_path(self, classification, lang, dest_type='page'):
        """Return a path for the given classification."""
        components = [self.site.config['ARCHIVE_PATH'](lang)]
        if classification:
            components.extend(classification)
            add_index = 'always'
        else:
            components.append(self.site.config['ARCHIVE_FILENAME'](lang))
            add_index = 'never'
        return [_f for _f in components if _f], add_index

    def extract_hierarchy(self, classification):
        """Given a classification, return a list of parts in the hierarchy."""
        return classification.split('/') if classification else []

    def recombine_classification_from_hierarchy(self, hierarchy):
        """Given a list of parts in the hierarchy, return the classification string."""
        return '/'.join(hierarchy)

    def provide_context_and_uptodate(self, classification, lang, node=None):
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
        elif len(hierarchy) == 1:
            title = kw["messages"][lang]["Posts for year %s"] % hierarchy[0]
        elif len(hierarchy) == 2:
            title = nikola.utils.LocaleBorg().format_date_in_string(
                kw["messages"][lang]["Posts for {month_year}"],
                datetime.date(int(hierarchy[0]), int(hierarchy[1]), 1),
                lang)
        elif len(hierarchy) == 3:
            title = nikola.utils.LocaleBorg().format_date_in_string(
                kw["messages"][lang]["Posts for {month_day_year}"],
                datetime.date(int(hierarchy[0]), int(hierarchy[1]), int(hierarchy[2])),
                lang)
        else:
            raise Exception("Cannot interpret classification {}!".format(repr(classification)))

        context = {
            "title": title,
            "pagekind": [page_kind, "archive_page"],
            "create_archive_navigation": self.site.config["CREATE_ARCHIVE_NAVIGATION"],
            "archive_name": classification
        }

        # Generate links for hierarchies
        if context["create_archive_navigation"]:
            if hierarchy:
                # Up level link makes sense only if this is not the top-level
                # page (hierarchy is empty)
                parent = '/'.join(hierarchy[:-1])
                context["up_archive"] = self.site.link('archive', parent, lang)
                context["up_archive_name"] = self.get_classification_friendly_name(parent, lang)
            else:
                context["up_archive"] = None
                context["up_archive_name"] = None

            nodelevel = len(hierarchy)
            flat_samelevel = self.archive_navigation[lang][nodelevel]
            idx = flat_samelevel.index(classification)
            if idx == -1:
                raise Exception("Cannot find classification {0} in flat hierarchy!".format(classification))
            previdx, nextidx = idx - 1, idx + 1
            # If the previous index is -1, or the next index is 1, the previous/next archive does not exist.
            context["previous_archive"] = self.site.link('archive', flat_samelevel[previdx], lang) if previdx != -1 else None
            context["previous_archive_name"] = self.get_classification_friendly_name(flat_samelevel[previdx], lang) if previdx != -1 else None
            context["next_archive"] = self.site.link('archive', flat_samelevel[nextidx], lang) if nextidx != len(flat_samelevel) else None
            context["next_archive_name"] = self.get_classification_friendly_name(flat_samelevel[nextidx], lang) if nextidx != len(flat_samelevel) else None
            context["archive_nodelevel"] = nodelevel
            context["has_archive_navigation"] = bool(context["previous_archive"] or context["up_archive"] or context["next_archive"])
        else:
            context["has_archive_navigation"] = False
        kw.update(context)
        return context, kw

    def postprocess_posts_per_classification(self, posts_per_classification_per_language, flat_hierarchy_per_lang=None, hierarchy_lookup_per_lang=None):
        """Rearrange, modify or otherwise use the list of posts per classification and per language."""
        # Build a lookup table for archive navigation, if we’ll need one.
        if self.site.config['CREATE_ARCHIVE_NAVIGATION']:
            if flat_hierarchy_per_lang is None:
                raise ValueError('Archives need flat_hierarchy_per_lang')
            self.archive_navigation = {}
            for lang, flat_hierarchy in flat_hierarchy_per_lang.items():
                self.archive_navigation[lang] = defaultdict(list)
                for node in flat_hierarchy:
                    if not self.site.config["SHOW_UNTRANSLATED_POSTS"]:
                        if not [x for x in posts_per_classification_per_language[lang][node.classification_name] if x.is_translation_available(lang)]:
                            continue
                    self.archive_navigation[lang][len(node.classification_path)].append(node.classification_name)

                # We need to sort it. Natsort means it’s year 10000 compatible!
                for k, v in self.archive_navigation[lang].items():
                    self.archive_navigation[lang][k] = natsort.natsorted(v, alg=natsort.ns.F | natsort.ns.IC)

        return super().postprocess_posts_per_classification(posts_per_classification_per_language, flat_hierarchy_per_lang, hierarchy_lookup_per_lang)

    def should_generate_classification_page(self, classification, post_list, lang):
        """Only generates list of posts for classification if this function returns True."""
        return classification == '' or len(post_list) > 0

    def get_other_language_variants(self, classification, lang, classifications_per_language):
        """Return a list of variants of the same classification in other languages."""
        return [(other_lang, classification) for other_lang, lookup in classifications_per_language.items() if classification in lookup and other_lang != lang]
