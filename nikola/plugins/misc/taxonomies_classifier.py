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

"""Render the taxonomy overviews, classification pages and feeds."""

from __future__ import unicode_literals
import blinker
import functools
import natsort
import os
import sys

from collections import defaultdict

from nikola.plugin_categories import SignalHandler
from nikola import utils


class TaxonomiesClassifier(SignalHandler):
    """Classify posts and pages by taxonomies."""

    name = "classify_taxonomies"

    def _do_classification(self, site):
        # Needed to avoid strange errors during tests
        if site is not self.site:
            return

        # Get list of enabled taxonomy plugins and initialize data structures
        taxonomies = site.taxonomy_plugins.values()
        site.posts_per_classification = {}
        for taxonomy in taxonomies:
            site.posts_per_classification[taxonomy.classification_name] = {
                lang: defaultdict(set) for lang in site.config['TRANSLATIONS'].keys()
            }

        # Classify posts
        for post in site.timeline:
            # Do classify pages, but don’t classify posts that are hidden
            # (draft/private/future)
            if post.is_post and not post.use_in_feeds:
                continue
            for taxonomy in taxonomies:
                if taxonomy.apply_to_posts if post.is_post else taxonomy.apply_to_pages:
                    classifications = {}
                    for lang in site.config['TRANSLATIONS'].keys():
                        # Extract classifications for this language
                        classifications[lang] = taxonomy.classify(post, lang)
                        if not taxonomy.more_than_one_classifications_per_post and len(classifications[lang]) > 1:
                            raise ValueError("Too many {0} classifications for post {1}".format(taxonomy.classification_name, post.source_path))
                        # Add post to sets
                        for classification in classifications[lang]:
                            while True:
                                site.posts_per_classification[taxonomy.classification_name][lang][classification].add(post)
                                if not taxonomy.include_posts_from_subhierarchies or not taxonomy.has_hierarchy:
                                    break
                                classification_path = taxonomy.extract_hierarchy(classification)
                                if len(classification_path) <= 1:
                                    if len(classification_path) == 0 or not taxonomy.include_posts_into_hierarchy_root:
                                        break
                                classification = taxonomy.recombine_classification_from_hierarchy(classification_path[:-1])

        # Sort everything.
        site.page_count_per_classification = {}
        site.hierarchy_per_classification = {}
        site.flat_hierarchy_per_classification = {}
        site.hierarchy_lookup_per_classification = {}
        for taxonomy in taxonomies:
            site.page_count_per_classification[taxonomy.classification_name] = {}
            # Sort post lists
            for lang, posts_per_classification in site.posts_per_classification[taxonomy.classification_name].items():
                # Ensure implicit classifications are inserted
                for classification in taxonomy.get_implicit_classifications(lang):
                    if classification not in posts_per_classification:
                        posts_per_classification[classification] = []
                site.page_count_per_classification[taxonomy.classification_name][lang] = {}
                # Convert sets to lists and sort them
                for classification in list(posts_per_classification.keys()):
                    posts = list(posts_per_classification[classification])
                    posts = self.site.sort_posts_chronologically(posts, lang)
                    taxonomy.sort_posts(posts, classification, lang)
                    posts_per_classification[classification] = posts
            # Create hierarchy information
            if taxonomy.has_hierarchy:
                site.hierarchy_per_classification[taxonomy.classification_name] = {}
                site.flat_hierarchy_per_classification[taxonomy.classification_name] = {}
                site.hierarchy_lookup_per_classification[taxonomy.classification_name] = {}
                for lang, posts_per_classification in site.posts_per_classification[taxonomy.classification_name].items():
                    # Compose hierarchy
                    hierarchy = {}
                    for classification in posts_per_classification.keys():
                        hier = taxonomy.extract_hierarchy(classification)
                        node = hierarchy
                        for he in hier:
                            if he not in node:
                                node[he] = {}
                            node = node[he]
                    hierarchy_lookup = {}

                    def create_hierarchy(hierarchy, parent=None, level=0):
                        """Create hierarchy."""
                        result = {}
                        for name, children in hierarchy.items():
                            node = utils.TreeNode(name, parent)
                            node.children = create_hierarchy(children, node, level + 1)
                            node.classification_path = [pn.name for pn in node.get_path()]
                            node.classification_name = taxonomy.recombine_classification_from_hierarchy(node.classification_path)
                            hierarchy_lookup[node.classification_name] = node
                            result[node.name] = node
                        classifications = natsort.natsorted(result.keys(), alg=natsort.ns.F | natsort.ns.IC)
                        taxonomy.sort_classifications(classifications, lang, level=level)
                        return [result[classification] for classification in classifications]

                    root_list = create_hierarchy(hierarchy)
                    if '' in posts_per_classification:
                        node = utils.TreeNode('', parent=None)
                        node.children = root_list
                        node.classification_path = []
                        node.classification_name = ''
                        hierarchy_lookup[node.name] = node
                        root_list = [node]
                    flat_hierarchy = utils.flatten_tree_structure(root_list)
                    # Store result
                    site.hierarchy_per_classification[taxonomy.classification_name][lang] = root_list
                    site.flat_hierarchy_per_classification[taxonomy.classification_name][lang] = flat_hierarchy
                    site.hierarchy_lookup_per_classification[taxonomy.classification_name][lang] = hierarchy_lookup
                taxonomy.postprocess_posts_per_classification(site.posts_per_classification[taxonomy.classification_name],
                                                              site.flat_hierarchy_per_classification[taxonomy.classification_name],
                                                              site.hierarchy_lookup_per_classification[taxonomy.classification_name])
            else:
                taxonomy.postprocess_posts_per_classification(site.posts_per_classification[taxonomy.classification_name])

        # Check for valid paths and for collisions
        taxonomy_outputs = {lang: dict() for lang in site.config['TRANSLATIONS'].keys()}
        quit = False
        for taxonomy in taxonomies:
            # Check for collisions (per language)
            for lang in site.config['TRANSLATIONS'].keys():
                if not taxonomy.is_enabled(lang):
                    continue
                for tlang in site.config['TRANSLATIONS'].keys():
                    if lang != tlang and not taxonomy.also_create_classifications_from_other_languages:
                        continue
                    for classification, posts in site.posts_per_classification[taxonomy.classification_name][tlang].items():
                        # Obtain path as tuple
                        path = site.path_handlers[taxonomy.classification_name](classification, lang)
                        # Check that path is OK
                        for path_element in path:
                            if len(path_element) == 0:
                                utils.LOGGER.error("{0} {1} yields invalid path '{2}'!".format(taxonomy.classification_name.title(), classification, '/'.join(path)))
                                quit = True
                        # Combine path
                        path = os.path.join(*[os.path.normpath(p) for p in path if p != '.'])
                        # Determine collisions
                        if path in taxonomy_outputs[lang]:
                            other_classification_name, other_classification, other_posts = taxonomy_outputs[lang][path]
                            if other_classification_name == taxonomy.classification_name and other_classification == classification:
                                taxonomy_outputs[lang][path][2].extend(posts)
                            else:
                                utils.LOGGER.error('You have classifications that are too similar: {0} "{1}" and {2} "{3}" both result in output path {4} for language {5}.'.format(
                                    taxonomy.classification_name, classification, other_classification_name, other_classification, path, lang))
                                utils.LOGGER.error('{0} {1} is used in: {2}'.format(
                                    taxonomy.classification_name.title(), classification, ', '.join(sorted([p.source_path for p in posts]))))
                                utils.LOGGER.error('{0} {1} is used in: {2}'.format(
                                    other_classification_name.title(), other_classification, ', '.join(sorted([p.source_path for p in other_posts]))))
                                quit = True
                        else:
                            taxonomy_outputs[lang][path] = (taxonomy.classification_name, classification, list(posts))
        if quit:
            sys.exit(1)
        blinker.signal('taxonomies_classified').send(site)

    def _get_filtered_list(self, taxonomy, classification, lang):
        """Return the filtered list of posts for this classification and language."""
        post_list = self.site.posts_per_classification[taxonomy.classification_name][lang].get(classification, [])
        if self.site.config["SHOW_UNTRANSLATED_POSTS"]:
            return post_list
        else:
            return [x for x in post_list if x.is_translation_available(lang)]

    @staticmethod
    def _compute_number_of_pages(filtered_posts, posts_count):
        """Given a list of posts and the maximal number of posts per page, computes the number of pages needed."""
        return min(1, (len(filtered_posts) + posts_count - 1) // posts_count)

    def _postprocess_path(self, path, lang, append_index='auto', dest_type='page', page_info=None, alternative_path=False):
        """Postprocess a generated path.

        Takes the path `path` for language `lang`, and postprocesses it.

        It appends `site.config['INDEX_FILE']` depending on `append_index`
        (which can have the values `'always'`, `'never'` and `'auto'`) and
        `site.config['PRETTY_URLS']`.

        It also modifies/adds the extension of the last path element resp.
        `site.config['INDEX_FILE']` depending on `dest_type`, which can be
        `'feed'`, `'rss'` or `'page'`.

        If `dest_type` is `'page'`, `page_info` can be `None` or a tuple
        of two integers: the page number and the number of pages. This will
        be used to append the correct page number by calling
        `utils.adjust_name_for_index_path_list` and
        `utils.get_displayed_page_number`.

        If `alternative_path` is set to `True`, `utils.adjust_name_for_index_path_list`
        is called with `force_addition=True`, resulting in an alternative path for the
        first page of an index or Atom feed by including the page number into the path.
        """
        # Forcing extension for Atom feeds and RSS feeds
        force_extension = None
        if dest_type == 'feed':
            force_extension = '.atom'
        elif dest_type == 'rss':
            force_extension = '.xml'
        # Determine how to extend path
        path = [_f for _f in path if _f]
        if force_extension is not None:
            if len(path) == 0 and dest_type == 'rss':
                path = ['rss']
            elif len(path) == 0 or append_index == 'always':
                path = path + [os.path.splitext(self.site.config['INDEX_FILE'])[0]]
            elif len(path) > 0 and append_index == 'never':
                path[-1] = os.path.splitext(path[-1])[0]
            path[-1] += force_extension
        elif (self.site.config['PRETTY_URLS'] and append_index != 'never') or len(path) == 0 or append_index == 'always':
            path = path + [self.site.config['INDEX_FILE']]
        elif append_index != 'never':
            path[-1] += '.html'
        # Create path
        result = [_f for _f in [self.site.config['TRANSLATIONS'][lang]] + path if _f]
        if page_info is not None and dest_type in ('page', 'feed'):
            result = utils.adjust_name_for_index_path_list(result,
                                                           page_info[0],
                                                           utils.get_displayed_page_number(page_info[0], page_info[1], self.site),
                                                           lang,
                                                           self.site, force_addition=alternative_path, extension=force_extension)
        return result

    @staticmethod
    def _parse_path_result(result):
        """Interpret the return values of taxonomy.get_path() and taxonomy.get_overview_path() as if all three return values were given."""
        if not isinstance(result[0], (list, tuple)):
            # The result must be a list or tuple of strings. Wrap into a tuple
            result = (result, )
        path = result[0]
        append_index = result[1] if len(result) > 1 else 'auto'
        page_info = result[2] if len(result) > 2 else None
        return path, append_index, page_info

    def _taxonomy_index_path(self, name, lang, taxonomy):
        """Return path to the classification overview."""
        result = taxonomy.get_overview_path(lang)
        path, append_index, _ = self._parse_path_result(result)
        return self._postprocess_path(path, lang, append_index=append_index, dest_type='list')

    def _taxonomy_path(self, name, lang, taxonomy, dest_type='page', page=None, alternative_path=False):
        """Return path to a classification."""
        if taxonomy.has_hierarchy:
            result = taxonomy.get_path(taxonomy.extract_hierarchy(name), lang, dest_type=dest_type)
        else:
            result = taxonomy.get_path(name, lang, dest_type=dest_type)
        path, append_index, page_ = self._parse_path_result(result)

        if page is not None:
            page = int(page)
        else:
            page = page_

        page_info = None
        if taxonomy.show_list_as_index and page is not None:
            number_of_pages = self.site.page_count_per_classification[taxonomy.classification_name][lang].get(name)
            if number_of_pages is None:
                number_of_pages = self._compute_number_of_pages(self._get_filtered_list(taxonomy, name, lang), self.site.config['INDEX_DISPLAY_POST_COUNT'])
                self.site.page_count_per_classification[taxonomy.classification_name][lang][name] = number_of_pages
            page_info = (page, number_of_pages)
        return self._postprocess_path(path, lang, append_index=append_index, dest_type=dest_type, page_info=page_info)

    def _taxonomy_atom_path(self, name, lang, taxonomy, page=None, alternative_path=False):
        """Return path to a classification Atom feed."""
        return self._taxonomy_path(name, lang, taxonomy, dest_type='feed', page=page, alternative_path=alternative_path)

    def _taxonomy_rss_path(self, name, lang, taxonomy):
        """Return path to a classification RSS feed."""
        return self._taxonomy_path(name, lang, taxonomy, dest_type='rss')

    def _register_path_handlers(self, taxonomy):
        functions = (
            ('{0}_index', self._taxonomy_index_path),
            ('{0}', self._taxonomy_path),
            ('{0}_atom', self._taxonomy_atom_path),
            ('{0}_rss', self._taxonomy_rss_path),
        )

        for name, function in functions:
            name = name.format(taxonomy.classification_name)
            p = functools.partial(function, taxonomy=taxonomy)
            doc = taxonomy.path_handler_docstrings[name]
            if doc is not False:
                p.__doc__ = doc
                self.site.register_path_handler(name, p)

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        super(TaxonomiesClassifier, self).set_site(site)
        # Add hook for after post scanning
        blinker.signal("scanned").connect(self._do_classification)
        # Register path handlers
        for taxonomy in site.taxonomy_plugins.values():
            self._register_path_handlers(taxonomy)
