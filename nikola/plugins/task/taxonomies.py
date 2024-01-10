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

"""Render the taxonomy overviews, classification pages and feeds."""

import os
from collections import defaultdict
from copy import copy
from urllib.parse import urljoin

import blinker
import natsort

from nikola import utils, hierarchy_utils
from nikola.nikola import _enclosure
from nikola.plugin_categories import Task


class RenderTaxonomies(Task):
    """Render taxonomy pages and feeds."""

    name = "render_taxonomies"

    def _generate_classification_overview_kw_context(self, taxonomy, lang):
        """Create context and kw for a classification overview page."""
        context, kw = taxonomy.provide_overview_context_and_uptodate(lang)

        context = copy(context)
        context["kind"] = "{}_index".format(taxonomy.classification_name)
        sorted_links = []
        for other_lang in sorted(self.site.config['TRANSLATIONS'].keys()):
            if other_lang != lang:
                sorted_links.append((other_lang, None, None))
        # Put the current language in front, so that it appears first in links
        # (Issue #3248)
        sorted_links_all = [(lang, None, None)] + sorted_links
        context['has_other_languages'] = True
        context['other_languages'] = sorted_links
        context['all_languages'] = sorted_links_all

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

            clipped_root_list = [hierarchy_utils.clone_treenode(node, parent=None, acceptor=acceptor) for node in self.site.hierarchy_per_classification[taxonomy.classification_name][lang]]
            clipped_root_list = [node for node in clipped_root_list if node]
            clipped_flat_hierarchy = hierarchy_utils.flatten_tree_structure(clipped_root_list)

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
        blinker.signal('generate_classification_overview').send({
            'site': self.site,
            'classification_name': classification_name,
            'lang': lang,
            'context': context,
            'kw': kw,
            'output_name': output_name,
        })
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
        """Render an index page collection using only this classification's posts."""
        kind = taxonomy.classification_name

        def page_link(i, displayed_i, num_pages, force_addition, extension=None):
            return self.site.link(kind, classification, lang, alternative_path=force_addition, page=i)

        def page_path(i, displayed_i, num_pages, force_addition, extension=None):
            return self.site.path(kind, classification, lang, alternative_path=force_addition, page=i)

        context = copy(context)
        context["kind"] = kind
        if "pagekind" not in context:
            context["pagekind"] = ["index", "tag_page"]
        template_name = taxonomy.template_for_single_list

        yield self.site.generic_index_renderer(lang, filtered_posts, context['title'], template_name, context, kw, str(self.name), page_link, page_path)

    def _generate_classification_page_as_atom(self, taxonomy, classification, filtered_posts, context, kw, lang):
        """Generate atom feeds for classification lists."""
        kind = taxonomy.classification_name

        context = copy(context)
        context["kind"] = kind

        yield self.site.generic_atom_renderer(lang, filtered_posts, context, kw, str(self.name), classification, kind)

    def _generate_classification_page_as_list(self, taxonomy, classification, filtered_posts, context, kw, lang):
        """Render a single flat link list with this classification's posts."""
        kind = taxonomy.classification_name
        template_name = taxonomy.template_for_single_list
        output_name = os.path.join(self.site.config['OUTPUT_FOLDER'], self.site.path(kind, classification, lang))
        context["lang"] = lang
        # list.tmpl expects a different format than list_post.tmpl (Issue #2701)
        if template_name == 'list.tmpl':
            context["items"] = [(post.title(lang), post.permalink(lang), None) for post in filtered_posts]
        else:
            context["posts"] = filtered_posts
        if "pagekind" not in context:
            context["pagekind"] = ["list", "tag_page"]
        task = self.site.generic_post_list_renderer(lang, filtered_posts, output_name, template_name, kw['filters'], context)
        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.taxonomies:list')]
        task['basename'] = str(self.name)
        yield task

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

    def _generate_classification_page(self, taxonomy, classification, filtered_posts, generate_list, generate_rss, generate_atom, lang, post_lists_per_lang, classification_set_per_lang=None):
        """Render index or post list and associated feeds per classification."""
        # Should we create this list?
        if not any((generate_list, generate_rss, generate_atom)):
            return
        # Get data
        node = None
        if taxonomy.has_hierarchy:
            node = self.site.hierarchy_lookup_per_classification[taxonomy.classification_name][lang].get(classification)
        context, kw = taxonomy.provide_context_and_uptodate(classification, lang, node)
        kw = copy(kw)
        kw["messages"] = self.site.MESSAGES
        kw["translations"] = self.site.config['TRANSLATIONS']
        kw["filters"] = self.site.config['FILTERS']
        kw["site_url"] = self.site.config['SITE_URL']
        kw["blog_title"] = self.site.config['BLOG_TITLE']
        kw["generate_rss"] = self.site.config['GENERATE_RSS']
        kw["generate_atom"] = self.site.config['GENERATE_ATOM']
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
        context["kind"] = taxonomy.classification_name
        # Get links to other language versions of this classification
        if classification_set_per_lang is not None:
            other_lang_links = taxonomy.get_other_language_variants(classification, lang, classification_set_per_lang)
            # Collect by language
            links_per_lang = defaultdict(list)
            for other_lang, link in other_lang_links:
                # Make sure we ignore the current language (in case the
                # plugin accidentally returns links for it as well)
                if other_lang != lang:
                    links_per_lang[other_lang].append(link)
            # Sort first by language, then by classification
            sorted_links = []
            sorted_links_all = []
            for other_lang in sorted(list(links_per_lang.keys()) + [lang]):
                if other_lang == lang:
                    sorted_links_all.append((lang, classification, taxonomy.get_classification_friendly_name(classification, lang)))
                else:
                    links = hierarchy_utils.sort_classifications(taxonomy, links_per_lang[other_lang], other_lang)
                    links = [(other_lang, other_classification,
                              taxonomy.get_classification_friendly_name(other_classification, other_lang))
                             for other_classification in links if post_lists_per_lang[other_lang].get(other_classification, ('', False, False))[1]]
                    sorted_links.extend(links)
                    sorted_links_all.extend(links)
            # Store result in context and kw
            context['has_other_languages'] = True
            context['other_languages'] = sorted_links
            context['all_languages'] = sorted_links_all
            kw['other_languages'] = sorted_links
            kw['all_languages'] = sorted_links_all
        else:
            context['has_other_languages'] = False
        # Allow other plugins to modify the result
        blinker.signal('generate_classification_page').send({
            'site': self.site,
            'taxonomy': taxonomy,
            'classification': classification,
            'lang': lang,
            'posts': filtered_posts,
            'context': context,
            'kw': kw,
        })
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

        # Generate Atom feed
        if generate_atom and kw["generate_atom"] and not taxonomy.always_disable_atom:
            yield self._generate_classification_page_as_atom(taxonomy, classification, filtered_posts, context, kw, lang)

        # Render HTML
        if generate_list and taxonomy.show_list_as_index:
            yield self._generate_classification_page_as_index(taxonomy, classification, filtered_posts, context, kw, lang)
        elif generate_list:
            yield self._generate_classification_page_as_list(taxonomy, classification, filtered_posts, context, kw, lang)

    def gen_tasks(self):
        """Render the tag pages and feeds."""
        self.site.scan_posts()
        yield self.group_task()

        # Cache classification sets per language for taxonomies where
        # add_other_languages_variable is True.
        classification_set_per_lang = {}
        for taxonomy in self.site.taxonomy_plugins.values():
            if taxonomy.add_other_languages_variable:
                lookup = self.site.posts_per_classification[taxonomy.classification_name]
                cspl = {lang: set(lookup[lang].keys()) for lang in lookup}
                classification_set_per_lang[taxonomy.classification_name] = cspl

        # Collect post lists for classification pages and determine whether
        # they should be generated.
        post_lists_per_lang = {}
        for taxonomy in self.site.taxonomy_plugins.values():
            plpl = {}
            for lang in self.site.config["TRANSLATIONS"]:
                result = {}
                for classification, posts in self.site.posts_per_classification[taxonomy.classification_name][lang].items():
                    # Filter list
                    filtered_posts = self._filter_list(posts, lang)
                    if len(filtered_posts) == 0 and taxonomy.omit_empty_classifications:
                        generate_list = generate_rss = generate_atom = False
                    else:
                        # Should we create this list?
                        generate_list = taxonomy.should_generate_classification_page(classification, filtered_posts, lang)
                        generate_rss = taxonomy.should_generate_rss_for_classification_page(classification, filtered_posts, lang)
                        generate_atom = taxonomy.should_generate_atom_for_classification_page(classification, filtered_posts, lang)
                    result[classification] = (filtered_posts, generate_list, generate_rss, generate_atom)
                plpl[lang] = result
            post_lists_per_lang[taxonomy.classification_name] = plpl

        # Now generate pages
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
                # Generate list of classifications (i.e. classification overview)
                if taxonomy not in ignore_plugins_for_overview:
                    if taxonomy.template_for_classification_overview is not None:
                        for task in self._generate_classification_overview(taxonomy, lang):
                            yield task

                # Process classifications
                for classification, (filtered_posts, generate_list, generate_rss, generate_atom) in post_lists_per_lang[taxonomy.classification_name][lang].items():
                    for task in self._generate_classification_page(taxonomy, classification, filtered_posts,
                                                                   generate_list, generate_rss, generate_atom, lang,
                                                                   post_lists_per_lang[taxonomy.classification_name],
                                                                   classification_set_per_lang.get(taxonomy.classification_name)):
                        yield task
            # In case we are ignoring plugins for overview, we must have a collision for
            # tags and categories. Handle this special case with extra code.
            if ignore_plugins_for_overview:
                for task in self._generate_tag_and_category_overview(self.site.taxonomy_plugins['tag'], self.site.taxonomy_plugins['category'], lang):
                    yield task
