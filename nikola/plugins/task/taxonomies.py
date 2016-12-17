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
import os
import natsort
from copy import copy
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA

from nikola.plugin_categories import Task
from nikola import utils
from nikola.nikola import _enclosure


class RenderTaxonomies(Task):
    """Render taxonomy pages and feeds."""

    name = "render_taxonomies"

    def _generate_classification_data(self, taxonomy, lang):
        """Create context and kw for a classification overview page."""
        # Collect all relevant classifications
        if taxonomy.has_hierarchy:
            # Create clipped tree
            def acceptor(node):
                return len(self._filter_list(self.site.posts_per_classification[taxonomy.classification_name][lang][node.classification_name], lang)) >= 1

            clipped_root_list = [_clone_treenode(node, parent=None, acceptor=acceptor) for node in self.site.hierarchy_per_classification[taxonomy.classification_name][lang]]
            clipped_root_list = [node for node in clipped_root_list if node]
            clipped_flat_hierarchy = utils.flatten_tree_structure(clipped_root_list)
            clipped_flat_lookup = {}
            clipped_node_lookup = {}
            for i, node in enumerate(clipped_flat_hierarchy):
                clipped_flat_lookup[node.classification_name] = i
                clipped_node_lookup[node.classification_name] = node

            classifications = [cat.classification_name for cat in clipped_flat_hierarchy]
        else:
            # Create and sort classifications
            classifications = natsort.natsorted([tag for tag, posts in self.site.posts_per_classification[taxonomy.classification_name][lang].items()
                                                 if len(self._filter_list(posts, lang)) >= 1],
                                                alg=natsort.ns.F | natsort.ns.IC)
            taxonomy.sort_classifications(classifications, lang)
            # No hierarchy
            clipped_root_list = None
            clipped_flat_hierarchy = None
            clipped_flat_lookup = None
            clipped_node_lookup = None
        # Create lookup for classifications
        classifications_lookup = {}
        for i, classification in enumerate(classifications):
            classifications_lookup[classification] = i
        # Store result
        if taxonomy.classification_name not in self.classification_data:
            self.classification_data[taxonomy.classification_name] = {lang: None for lang in self.site.config["TRANSLATIONS"]}
        self.classification_data[taxonomy.classification_name][lang] = classifications, classifications_lookup, clipped_root_list, clipped_flat_hierarchy, clipped_flat_lookup, clipped_node_lookup

    def _generate_classification_overview_kw_context(self, taxonomy, lang):
        """Create context and kw for a classification overview page."""
        context, kw = taxonomy.provide_overview_context_and_uptodate(lang)

        context = copy(context)
        kw = copy(kw)
        kw["messages"] = self.site.MESSAGES
        kw["translations"] = self.site.config['TRANSLATIONS']
        kw["filters"] = self.site.config['FILTERS']
        kw["minimum_post_count"] = taxonomy.minimum_post_count_per_classification_in_overview
        kw["output_folder"] = self.site.config['OUTPUT_FOLDER']
        kw["pretty_urls"] = self.site.config['PRETTY_URLS']
        kw["strip_indexes"] = self.site.config['STRIP_INDEXES']
        kw["index_file"] = self.site.config['INDEX_FILE']

        # Collect all relevant classifications
        if taxonomy.has_hierarchy:
            def acceptor(node):
                return len(self._filter_list(self.site.posts_per_classification[taxonomy.classification_name][lang][node.classification_name], lang)) >= kw["minimum_post_count"]

            clipped_root_list = [utils.clone_treenode(node, parent=None, acceptor=acceptor) for node in self.site.hierarchy_per_classification[taxonomy.classification_name][lang]]
            clipped_root_list = [node for node in clipped_root_list if node]
            clipped_flat_hierarchy = utils.flatten_tree_structure(clipped_root_list)

            classifications = [cat.classification_name for cat in clipped_flat_hierarchy]
        else:
            classifications = natsort.natsorted([tag for tag, posts in self.site.posts_per_classification[taxonomy.classification_name][lang].items()
                                                 if len(self._filter_list(posts, lang)) >= kw["minimum_post_count"]],
                                                alg=natsort.ns.F | natsort.ns.IC)
            taxonomy.sort_classifications(classifications, lang)

        # Set up classifications in context
        context[taxonomy.overview_page_variable_name] = classifications
        context["has_hierarchy"] = taxonomy.has_hierarchy
        if taxonomy.overview_page_items_variable_name:
            items = [(classification,
                      self.site.link(taxonomy.classification_name, classification, lang))
                     for classification in classifications]
            items_with_postcount = [
                (classification,
                 self.site.link(taxonomy.classification_name, classification, lang),
                 len(self._filter_list(self.site.posts_per_classification[taxonomy.classification_name][lang][classification], lang)))
                for classification in classifications
            ]
            context[taxonomy.overview_page_items_variable_name] = items
            context[taxonomy.overview_page_items_variable_name + "_with_postcount"] = items_with_postcount
        if taxonomy.has_hierarchy and taxonomy.overview_page_hierarchy_variable_name:
            hier_items = [
                (node.name, node.classification_name, node.classification_path,
                 self.site.link(taxonomy.classification_name, node.classification_name, lang),
                 node.indent_levels, node.indent_change_before,
                 node.indent_change_after)
                for node in clipped_flat_hierarchy
            ]
            hier_items_with_postcount = [
                (node.name, node.classification_name, node.classification_path,
                 self.site.link(taxonomy.classification_name, node.classification_name, lang),
                 node.indent_levels, node.indent_change_before,
                 node.indent_change_after,
                 len(node.children),
                 len(self._filter_list(self.site.posts_per_classification[taxonomy.classification_name][lang][node.classification_name], lang)))
                for node in clipped_flat_hierarchy
            ]
            context[taxonomy.overview_page_hierarchy_variable_name] = hier_items
            context[taxonomy.overview_page_hierarchy_variable_name + '_with_postcount'] = hier_items_with_postcount
        return context, kw

    def _render_classification_overview(self, classification_name, template, lang, context, kw):
        # Prepare rendering
        context["permalink"] = self.site.link("{}_index".format(classification_name), None, lang)
        if "pagekind" not in context:
            context["pagekind"] = ["list", "tags_page"]
        output_name = os.path.join(self.site.config['OUTPUT_FOLDER'], self.site.path('{}_index'.format(classification_name), None, lang))
        task = self.site.generic_post_list_renderer(
            lang,
            [],
            output_name,
            template,
            kw['filters'],
            context,
        )
        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.taxonomies:page')]
        task['basename'] = str(self.name)
        yield task

    def _generate_classification_overview(self, taxonomy, lang):
        """Create a global "all your tags/categories" page for a given language."""
        context, kw = self._generate_classification_overview_kw_context(taxonomy, lang)
        for task in self._render_classification_overview(taxonomy.classification_name, taxonomy.template_for_classification_overview, lang, context, kw):
            yield task

    def _generate_tag_and_category_overview(self, tag_taxonomy, category_taxonomy, lang):
        """Create a global "all your tags/categories" page for a given language."""
        # Create individual contexts and kw dicts
        tag_context, tag_kw = self._generate_classification_overview_kw_context(tag_taxonomy, lang)
        cat_context, cat_kw = self._generate_classification_overview_kw_context(category_taxonomy, lang)

        # Combine resp. select dicts
        if tag_context['items'] and cat_context['cat_items']:
            # Combine contexts. We must merge the tag context into the category context
            # so that tag_context['items'] makes it into the result.
            context = cat_context
            context.update(tag_context)
            kw = cat_kw
            kw.update(tag_kw)

            # Update title
            title = self.site.MESSAGES[lang]["Tags and Categories"]
            context['title'] = title
            context['description'] = title
            kw['title'] = title
            kw['description'] = title
        elif cat_context['cat_items']:
            # Use category overview page
            context = cat_context
            kw = cat_kw
        else:
            # Use tag overview page
            context = tag_context
            kw = tag_kw

        # Render result
        for task in self._render_classification_overview('tag', tag_taxonomy.template_for_classification_overview, lang, context, kw):
            yield task

    def _generate_classification_page_as_rss(self, taxonomy, classification, filtered_posts, title, description, kw, lang):
        """Create a RSS feed for a single classification in a given language."""
        kind = taxonomy.classification_name
        # Render RSS
        output_name = os.path.normpath(os.path.join(self.site.config['OUTPUT_FOLDER'], self.site.path(kind + "_rss", classification, lang)))
        feed_url = urljoin(self.site.config['BASE_URL'], self.site.link(kind + "_rss", classification, lang).lstrip('/'))
        deps = []
        deps_uptodate = []
        for post in filtered_posts:
            deps += post.deps(lang)
            deps_uptodate += post.deps_uptodate(lang)
        blog_title = kw["blog_title"](lang)
        task = {
            'basename': str(self.name),
            'name': output_name,
            'file_dep': deps,
            'targets': [output_name],
            'actions': [(utils.generic_rss_renderer,
                        (lang, "{0} ({1})".format(blog_title, title) if blog_title != title else blog_title,
                         kw["site_url"], description, filtered_posts,
                         output_name, kw["feed_teasers"], kw["feed_plain"], kw['feed_length'],
                         feed_url, _enclosure, kw["feed_links_append_query"]))],
            'clean': True,
            'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.taxonomies:rss')] + deps_uptodate,
            'task_dep': ['render_posts'],
        }
        return utils.apply_filters(task, kw['filters'])

    def _generate_classification_page_as_index(self, taxonomy, classification, filtered_posts, context, kw, lang):
        """Render a sort of index page collection using only this classification's posts."""
        kind = taxonomy.classification_name

        def page_link(i, displayed_i, num_pages, force_addition, extension=None):
            feed = "{}_atom" if extension == ".atom" else "{}"
            return self.site.link(feed.format(kind), classification, lang, alternative_path=force_addition, page=i)

        def page_path(i, displayed_i, num_pages, force_addition, extension=None):
            feed = "{}_atom" if extension == ".atom" else "{}"
            return self.site.path(feed.format(kind), classification, lang, alternative_path=force_addition, page=i)

        context = copy(context)
        if "pagekind" not in context:
            context["pagekind"] = ["index", "tag_page"]
        template_name = taxonomy.template_for_single_list

        yield self.site.generic_index_renderer(lang, filtered_posts, context['title'], template_name, context, kw, str(self.name), page_link, page_path)

    def _generate_classification_page_as_list_atom(self, taxonomy, classification, filtered_posts, context, kw, lang):
        """Generate atom feeds for classification lists."""
        kind = taxonomy.classification_name
        context = copy(context)
        context['feedlink'] = self.site.abs_link(self.site.path('{}_atom'.format(kind), classification, lang))
        feed_path = os.path.join(self.site.config['OUTPUT_FOLDER'], self.site.path('{}_atom'.format(kind), classification, lang))

        task = {
            'basename': str(self.name),
            'name': feed_path,
            'targets': [feed_path],
            'actions': [(self.site.atom_feed_renderer, (lang, filtered_posts, feed_path, kw['filters'], context))],
            'clean': True,
            'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.taxonomies:atom')],
            'task_dep': ['render_posts'],
        }
        return task

    def _generate_classification_page_as_list(self, taxonomy, classification, filtered_posts, context, kw, lang):
        """Render a single flat link list with this classification's posts."""
        kind = taxonomy.classification_name
        template_name = taxonomy.template_for_single_list
        output_name = os.path.join(self.site.config['OUTPUT_FOLDER'], self.site.path(kind, classification, lang))
        context["lang"] = lang
        context["posts"] = filtered_posts
        context["kind"] = kind
        if "pagekind" not in context:
            context["pagekind"] = ["list", "tag_page"]
        task = self.site.generic_post_list_renderer(lang, filtered_posts, output_name, template_name, kw['filters'], context)
        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.taxonomies:list')]
        task['basename'] = str(self.name)
        yield task

        if taxonomy.generate_atom_feeds_for_post_lists and self.site.config['GENERATE_ATOM']:
            yield self._generate_classification_page_as_list_atom(taxonomy, classification, filtered_posts, context, kw, lang)

    def _filter_list(self, post_list, lang):
        """Return only the posts which should be shown for this language."""
        if self.site.config["SHOW_UNTRANSLATED_POSTS"]:
            return post_list
        else:
            return [x for x in post_list if x.is_translation_available(lang)]

    def _generate_subclassification_page(self, taxonomy, node, context, kw, lang):
        """Render a list of subclassifications."""
        def get_subnode_data(subnode):
            return [
                taxonomy.get_classification_friendly_name(subnode.classification_name, lang, only_last_component=True),
                self.site.link(taxonomy.classification_name, subnode.classification_name, lang),
                len(self._filter_list(self.site.posts_per_classification[taxonomy.classification_name][lang][subnode.classification_name], lang))
            ]

        items = [get_subnode_data(subnode) for subnode in node.children]
        context = copy(context)
        context["lang"] = lang
        context["permalink"] = self.site.link(taxonomy.classification_name, node.classification_name, lang)
        if "pagekind" not in context:
            context["pagekind"] = ["list", "archive_page"]
        context["items"] = items
        task = self.site.generic_post_list_renderer(
            lang,
            [],
            os.path.join(kw['output_folder'], self.site.path(taxonomy.classification_name, node.classification_name, lang)),
            taxonomy.subcategories_list_template,
            kw['filters'],
            context,
        )
        task_cfg = {1: kw, 2: items}
        task['uptodate'] = task['uptodate'] + [utils.config_changed(task_cfg, 'nikola.plugins.task.taxonomy')]
        task['basename'] = self.name
        return task

    def _add_cross_classification_navigation_links(self, taxonomy, classification, context, kw, lang, generate_list, generate_rss):
        classifications, classifications_lookup, clipped_root_list, clipped_flat_hierarchy, clipped_flat_lookup, clipped_node_lookup = self.classification_data[taxonomy.classification_name][lang]
        # Get previous and next in (flattened) list of all classifications
        i = classifications_lookup.get(classification)
        if i is not None:
            previous_classification = classifications[i - 1] if i > 0 else None
            next_classification = classifications[i + 1] if i + 1 < len(classifications) else None
        else:
            previous_classification = None
            next_classification = None
        # Get hirearchical info
        parent = None
        if taxonomy.has_hierarchy:
            # Find siblings
            previous_sibling = None
            next_sibling = None
            node = clipped_node_lookup.get(classification)
            if node is not None:
                parent = node.parent.classification_name if node.parent is not None else None
                siblings = node.parent.children if node.parent is not None else clipped_root_list
                index = None
                for i, node in enumerate(siblings):
                    if node.classification_name == classification:
                        index = i
                if index is not None:
                    if index > 0:
                        previous_sibling = siblings[index - 1].classification_name
                    if index + 1 < len(siblings):
                        next_sibling = siblings[index + 1].classification_name
            # Find previous/next elements on same hierarchy level
            previous_samelevel = None
            next_samelevel = None
            i = clipped_flat_lookup.get(classification)
            if i is not None:
                # Find previous
                index = i - 1
                while index >= 0:
                    if len(clipped_flat_hierarchy[index].indent_levels) != len(clipped_flat_hierarchy[i].indent_levels):
                        index -= 1
                    else:
                        break
                if index >= 0:
                    previous_samelevel = clipped_flat_hierarchy[index].classification_name
                # Find next
                index = i + 1
                while index < len(clipped_flat_hierarchy):
                    if len(clipped_flat_hierarchy[index].indent_levels) != len(clipped_flat_hierarchy[i].indent_levels):
                        index += 1
                    else:
                        break
                if index < len(clipped_flat_hierarchy):
                    previous_samelevel = clipped_flat_hierarchy[index].classification_name
        else:
            previous_sibling = previous_classification
            next_sibling = next_classification
            previous_samelevel = previous_classification
            next_samelevel = next_classification
        # Get results
        result = {}

        def add(name, classification):
            result[name] = classification
            if classification is not None:
                result['{0}_name'.format(name)] = taxonomy.get_classification_friendly_name(classification, lang, only_last_component=False)
                if generate_list:
                    result['{0}_link'.format(name)] = self.site.link(taxonomy.classification_name, classification, lang)
                if generate_list and self.site.config['GENERATE_ATOM'] and taxonomy.show_list_as_index:
                    result['{0}_atom'.format(name)] = self.site.link('{0}_atom'.format(taxonomy.classification_name), classification, lang)
                if generate_rss and self.site.config['GENERATE_RSS'] and not taxonomy.always_disable_rss:
                    result['{0}_rss'.format(name)] = self.site.link('{0}_rss'.format(taxonomy.classification_name), classification, lang)

        add('previous_{0}'.format(taxonomy.classification_name), previous_classification)
        add('next_{0}'.format(taxonomy.classification_name), next_classification)
        add('previous_{0}_sibling'.format(taxonomy.classification_name), previous_sibling)
        add('next_{0}_sibling'.format(taxonomy.classification_name), next_sibling)
        add('previous_{0}_samelevel'.format(taxonomy.classification_name), previous_samelevel)
        add('next_{0}_samelevel'.format(taxonomy.classification_name), next_samelevel)
        add('parent_{0}'.format(taxonomy.classification_name), parent)
        # Update context and kw
        context.update(result)
        kw.update(result)

    def _generate_classification_page(self, taxonomy, classification, post_list, lang):
        """Render index or post list and associated feeds per classification."""
        # Filter list
        filtered_posts = self._filter_list(post_list, lang)
        if len(filtered_posts) == 0 and taxonomy.omit_empty_classifications:
            return
        # Should we create this list?
        generate_list = taxonomy.should_generate_classification_page(classification, filtered_posts, lang)
        generate_rss = taxonomy.should_generate_rss_for_classification_page(classification, filtered_posts, lang)
        if not generate_list and not generate_rss:
            return
        # Get data
        node = None
        if taxonomy.has_hierarchy:
            node = self.site.hierarchy_lookup_per_classification[taxonomy.classification_name][lang][classification]
        context, kw = taxonomy.provide_context_and_uptodate(classification, lang, node)
        kw = copy(kw)
        kw["messages"] = self.site.MESSAGES
        kw["translations"] = self.site.config['TRANSLATIONS']
        kw["filters"] = self.site.config['FILTERS']
        kw["site_url"] = self.site.config['SITE_URL']
        kw["blog_title"] = self.site.config['BLOG_TITLE']
        kw["generate_rss"] = self.site.config['GENERATE_RSS']
        kw["feed_teasers"] = self.site.config["FEED_TEASERS"]
        kw["feed_plain"] = self.site.config["FEED_PLAIN"]
        kw["feed_links_append_query"] = self.site.config["FEED_LINKS_APPEND_QUERY"]
        kw["feed_length"] = self.site.config['FEED_LENGTH']
        kw["output_folder"] = self.site.config['OUTPUT_FOLDER']
        kw["pretty_urls"] = self.site.config['PRETTY_URLS']
        kw["strip_indexes"] = self.site.config['STRIP_INDEXES']
        kw["index_file"] = self.site.config['INDEX_FILE']
        context = copy(context)
        context["permalink"] = self.site.link(taxonomy.classification_name, classification, lang)
        # Links to previous/next classifications
        self._add_cross_classification_navigation_links(taxonomy, classification, context, kw, lang, generate_list, generate_rss)
        # Decide what to do
        if taxonomy.has_hierarchy and taxonomy.show_list_as_subcategories_list:
            # Determine whether there are subcategories
            node = self.site.hierarchy_lookup_per_classification[taxonomy.classification_name][lang][classification]
            # Are there subclassifications?
            if len(node.children) > 0:
                # Yes: create list with subclassifications instead of list of posts
                if generate_list:
                    yield self._generate_subclassification_page(taxonomy, node, context, kw, lang)
                return
        # Generate RSS feed
        if generate_rss and kw["generate_rss"] and not taxonomy.always_disable_rss:
            yield self._generate_classification_page_as_rss(taxonomy, classification, filtered_posts, context['title'], context.get("description"), kw, lang)
        # Render HTML
        if generate_list and taxonomy.show_list_as_index:
            yield self._generate_classification_page_as_index(taxonomy, classification, filtered_posts, context, kw, lang)
        elif generate_list:
            yield self._generate_classification_page_as_list(taxonomy, classification, filtered_posts, context, kw, lang)

    def gen_tasks(self):
        """Render the tag pages and feeds."""
        self.site.scan_posts()
        yield self.group_task()

        self.classification_data = {}
        for lang in self.site.config["TRANSLATIONS"]:
            # To support that tag and category classifications share the same overview,
            # we explicitly detect this case:
            ignore_plugins_for_overview = set()
            if 'tag' in self.site.taxonomy_plugins and 'category' in self.site.taxonomy_plugins and self.site.link("tag_index", None, lang) == self.site.link("category_index", None, lang):
                # Block both plugins from creating overviews
                ignore_plugins_for_overview.add(self.site.taxonomy_plugins['tag'])
                ignore_plugins_for_overview.add(self.site.taxonomy_plugins['category'])
            for taxonomy in self.site.taxonomy_plugins.values():
                if not taxonomy.is_enabled(lang):
                    continue
                # Generate some data on classifications
                self._generate_classification_data(taxonomy, lang)
                # Generate list of classifications (i.e. classification overview)
                if taxonomy not in ignore_plugins_for_overview and taxonomy.template_for_classification_overview is not None:
                    for task in self._generate_classification_overview(taxonomy, lang):
                        yield task

                # Generate classification lists
                classifications = {}
                for tlang, posts_per_classification in self.site.posts_per_classification[taxonomy.classification_name].items():
                    if lang != tlang and not taxonomy.also_create_classifications_from_other_languages:
                        continue
                    classifications.update(posts_per_classification)

                # Process classifications
                for classification, posts in classifications.items():
                    for task in self._generate_classification_page(taxonomy, classification, posts, lang):
                        yield task
            # In case we are ignoring plugins for overview, we must have a collision for
            # tags and categories. Handle this special case with extra code.
            if ignore_plugins_for_overview:
                for task in self._generate_tag_and_category_overview(self.site.taxonomy_plugins['tag'], self.site.taxonomy_plugins['category'], lang):
                    yield task
