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

"""Render the taxonomy overviews, classification pages and feeds."""

from __future__ import unicode_literals
import blinker
import natsort
import os
import sys

from collections import defaultdict

from nikola.plugin_categories import SignalHandler
from nikola import utils


class TaxonomiesClassifier(SignalHandler):
    """Render the tag/category pages and feeds."""

    name = "render_taxonomies"

    def _do_classification(self):
        taxonomies = self.site.plugin_manager.getPluginsOfCategory('Taxonomy')
        self.site.posts_per_classification = {}
        for taxonomy in taxonomies:
            if taxonomy.classification_name in self.site.posts_per_classification:
                raise Exception("Found more than one taxonomy with classification name '{}'!".format(taxonomy.classification_name))
            self.site.posts_per_classification[taxonomy.classification_name] = {
                lang: defaultdict(set) for lang in self.config['TRANSLATIONS'].keys()
            }

        # Classify posts
        for post in self.timeline:
            for taxonomy in taxonomies:
                if taxonomy.apply_to_posts if post.is_post else taxonomy.apply_to_pages:
                    classifications = {}
                    for lang in self.config['TRANSLATIONS'].keys():
                        # Extract classifications for this language
                        classifications[lang] = taxonomy.classify(post, lang)
                        assert taxonomy.more_than_one_classifications_per_post or len(classifications[lang]) <= 1
                        # Store in metadata
                        if taxonomy.more_than_one_classifications_per_post:
                            post.meta[lang][taxonomy.metadata_name] = classifications[lang]
                        else:
                            post.meta[lang][taxonomy.metadata_name] = classifications[lang][0] if len(classifications[lang]) > 0 else None
                        # Add post to sets
                        for classification in classifications[lang]:
                            while classification:
                                self.site.posts_per_classification[taxonomy.classification_name][lang][classification].add(post)
                                if not taxonomy.include_posts_from_subhierarchies or not taxonomy.has_hierarchy:
                                    break
                                classification = taxonomy.recombine_classification_from_hierarchy(taxonomy.extract_hierarchy(classification)[:-1])

        # Check for valid paths and for collisions
        taxonomy_outputs = {lang: dict() for lang in self.config['TRANSLATIONS'].keys()}
        quit = False
        for taxonomy in taxonomies:
            # Check for collisions (per language)
            for lang in self.config['TRANSLATIONS'].keys():
                for tlang in self.config['TRANSLATIONS'].keys():
                    if lang != tlang and not taxonomy.also_create_classifications_from_other_languages:
                        continue
                    for classification, posts in self.site.posts_per_classification[taxonomy.classification_name][tlang].items():
                        # Obtain path as tuple
                        if taxonomy.has_hierarchy:
                            path = taxonomy.get_path(taxonomy.extract_hierarchy(classification), lang)
                        else:
                            path = taxonomy.get_path(classification, lang)
                        path = tuple(path)
                        # Check that path is OK
                        for path_element in path:
                            if len(path_element) == 0:
                                utils.LOGGER.error("{0} {1} yields invalid path '{2}'!".format(taxonomy.classification_name.title(), classification, '/'.join(path)))
                                quit = True
                        # Determine collisions
                        if path in taxonomy_outputs[lang]:
                            other_classification_name, other_classification, other_posts = taxonomy_outputs[lang][path]
                            utils.LOGGER.error('You have classifications that are too similar: {0} "{1}" and {1} "{2}"'.format(
                                taxonomy.classification_name, classification, other_classification_name, other_classification))
                            utils.LOGGER.error('{0} {1} is used in: {1}'.format(
                                taxonomy.classification_name.title(), classification, ', '.join(sorted([p.source_path for p in posts]))))
                            utils.LOGGER.error('{0} {1} is used in: {1}'.format(
                                other_classification_name.title(), other_classification, ', '.join(sorted([p.source_path for p in other_posts]))))
                            quit = True
                        else:
                            taxonomy_outputs[lang][path] = (taxonomy.classification_name, classification, posts)
        if quit:
            sys.exit(1)

        # Sort everything.
        self.site.hierarchy_per_classification = {}
        self.site.flat_hierarchy_per_classification = {}
        self.site.hierarchy_lookup_per_classification = {}
        for taxonomy in taxonomies:
            # Sort post lists
            for lang, posts_per_classification in self.site.posts_per_classification[taxonomy.classification_name].items():
                # Convert sets to lists and sort them
                for classification in list(posts_per_classification.keys()):
                    posts = list(posts_per_classification[classification])
                    posts.sort(key=lambda p:
                               (int(p.meta('priority')) if p.meta('priority') else 0,
                                p.date, p.source_path))
                    posts.reverse()
                    taxonomy.sort_posts(posts, classification, lang)
                    posts_per_classification[classification] = posts
            # Create hierarchy information
            if taxonomy.has_hierarchy:
                self.site.hierarchy_per_classification[taxonomy.classification_name] = {}
                self.site.flat_hierarchy_per_classification[taxonomy.classification_name] = {}
                self.site.hierarchy_lookup_per_classification[taxonomy.classification_name] = {}
                for lang, posts_per_classification in self.site.posts_per_classification[taxonomy.classification_name].items():
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

                    def create_hierarchy(cat_hierarchy, parent=None):
                        """Create category hierarchy."""
                        result = []
                        for name, children in cat_hierarchy.items():
                            node = utils.TreeNode(name, parent)
                            node.children = create_hierarchy(children, node)
                            node.classification_path = [pn.name for pn in node.get_path()]
                            node.classification_name = taxonomy.recombine_classification_from_hierarchy(node.classification_path)
                            hierarchy_lookup[node.classification_name] = node
                        classifications = natsort.natsorted(result, key=lambda e: e.name, alg=natsort.ns.F | natsort.ns.IC)
                        taxonomy.sort_classifications(classifications, lang)
                        return classifications

                    root_list = create_hierarchy(hierarchy)
                    flat_hierarchy = utils.flatten_tree_structure(root_list)
                    # Store result
                    self.site.hierarchy_per_classification[taxonomy.classification_name][lang] = root_list
                    self.site.flat_hierarchy_per_classification[taxonomy.classification_name][lang] = flat_hierarchy
                    self.site.hierarchy_lookup_per_classification[taxonomy.classification_name][lang] = hierarchy_lookup
                taxonomy.postprocess_posts_per_classification(self.site.posts_per_classification[taxonomy.classification_name],
                                                              self.site.flat_hierarchy_per_classification[taxonomy.classification_name],
                                                              self.site.hierarchy_lookup_per_classification[taxonomy.classification_name])
            else:
                taxonomy.postprocess_posts_per_classification(self.site.posts_per_classification[taxonomy.classification_name], flat_hierarchy, hierarchy_lookup)

        # Postprocessing
        for taxonomy in taxonomies:
            for lang, posts_per_classification in self.site.posts_per_classification[taxonomy.classification_name].items():
                taxonomy.postprocess_posts_per_classification(
                    posts_per_classification,
                    self.site.flat_hierarchy_per_classification.get(taxonomy.classification_name, {}).get(lang, None),
                    self.site.hierarchy_lookup_per_classification.get(taxonomy.classification_name, {}).get(lang, None),
                )

    def _postprocess_path(self, path, lang, force_extension=None):
        if force_extension is not None:
            if len(path) == 0:
                path = [os.path.splitext(self.site.config['INDEX_FILE'])[0]]
            path[-1] += force_extension
        elif self.site.config['PRETTY_URLS'] or len(path) == 0:
            path = path + [self.site.config['INDEX_FILE']]
        else:
            path[-1] += '.html'
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang]] + path if _f]

    def _taxonomy_index_path(self, lang, taxonomy):
        """Return path to the classification overview."""
        return self._postprocess_path(taxonomy.get_list_path(lang), lang)

    def _taxonomy_path(self, name, lang, taxonomy, force_extension=None):
        """Return path to a classification."""
        if taxonomy.has_hirearchy:
            path = taxonomy.get_path(taxonomy.extract_hierarchy(name), lang)
        else:
            path = taxonomy.get_path(name, lang)
        return self._postprocess_path(path, lang, force_extension=force_extension)

    def _taxonomy_atom_path(self, name, lang, taxonomy):
        """Return path to a classification Atom feed."""
        return self._taxonomy_path(name, lang, taxonomy, force_extension='.atom')

    def _taxonomy_rss_path(self, name, lang, taxonomy):
        """Return path to a classification RSS feed."""
        return self._taxonomy_path(name, lang, taxonomy, force_extension='.xml')

    def _register_path_handlers(self, taxonomy):
        self.site.register_path_handler('{0}_index'.format(taxonomy.classification_name), lambda name, lang: self._tag_index_path(lang, taxonomy))
        self.site.register_path_handler('{0}'.format(taxonomy.classification_name), lambda name, lang: self._tag_path(name, lang, taxonomy))
        self.site.register_path_handler('{0}_atom'.format(taxonomy.classification_name), lambda name, lang: self._tag_atom_path(name, lang, taxonomy))
        self.site.register_path_handler('{0}_rss'.format(taxonomy.classification_name), lambda name, lang: self._tag_rss_path(name, lang, taxonomy))

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        super(TaxonomiesClassifier, self).set_site(site)
        # Add hook for after post scanning
        blinker.signal("scanned").connect(self._do_classification)
        # Register path handlers
        for taxonomy in self.plugin_manager.getPluginsOfCategory('Taxonomy'):
            self._register_path_handlers(taxonomy)
