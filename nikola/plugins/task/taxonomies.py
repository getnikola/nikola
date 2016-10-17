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


def _clone_treenode(treenode, parent=None, acceptor=lambda x: True):
    # Standard TreeNode stuff
    node_clone = utils.TreeNode(treenode.name, parent)
    node_clone.children = [_clone_treenode(node, parent=node_clone, acceptor=acceptor) for node in treenode.children]
    node_clone.children = [node for node in node_clone.children if node]
    node_clone.indent_levels = treenode.indent_levels
    node_clone.indent_change_before = treenode.indent_change_before
    node_clone.indent_change_after = treenode.indent_change_after
    # Stuff added by extended_tags_preproces plugin
    node_clone.tag_path = treenode.tag_path
    node_clone.tag_name = treenode.tag_name
    # Accept this node if there are no children (left) and acceptor fails
    if not node_clone.children and not acceptor(treenode):
        return None
    return node_clone


class RenderTaxonomies(Task):
    """Render the tag/category pages and feeds."""

    name = "render_taxonomies"

    def _generate_classification_overview(self, taxonomy, lang):
        """Create a global "all your tags/categories" page for each language."""
        context, kw = taxonomy.provide_list_context_and_uptodate(lang)

        context = copy(context)
        kw = copy(kw)
        kw['filters'] = self.site.config['FILTERS']
        kw["minimum_post_count"] = taxonomy.minimum_post_count_per_classification_in_overview
        kw["output_folder"] = self.site.config['OUTPUT_FOLDER']

        # Collect all relevant classifications
        if taxonomy.has_hierarchy:
            def acceptor(node):
                return len(self.site.posts_per_classification[taxonomy.classification_name][lang][node.classification_name]) >= kw["minimum_post_count"]

            clipped_root_list = [_clone_treenode(node, parent=None, acceptor=acceptor) for node in self.site.hierarchy_per_classification[taxonomy.classification_name][lang]]
            clipped_root_list = [node for node in clipped_root_list if node]
            clipped_flat_hierarchy = utils.flatten_tree_structure(clipped_root_list)

            classifications = [cat.classification_name for cat in clipped_flat_hierarchy]
        else:
            classifications = natsort.natsorted([tag for tag, posts in self.site.posts_per_classification[taxonomy.classification_name][lang].items()
                                                 if len(posts) >= kw["minimum_post_count"]],
                                                alg=natsort.ns.F | natsort.ns.IC)
            taxonomy.sort_classifications(classifications, lang)

        # Set up classifications in context
        context[taxonomy.overview_page_variable_name] = classifications
        context["items"] = [(classification, self.site.link(taxonomy.classification_name, classification, lang)) for classification in classifications]
        context["has_hierarchy"] = taxonomy.has_hierarchy
        if taxonomy.has_hierarchy:
            context["hierarchy"] = [(node.name, node.classification_name, node.classification_path,
                                     self.site.link(taxonomy.classification_name, node.classification_name, lang),
                                     node.indent_levels, node.indent_change_before,
                                     node.indent_change_after)
                                    for node in clipped_flat_hierarchy]

        # Prepare rendering
        context["permalink"] = self.site.link("{}_index".format(taxonomy.classification_name), None, lang)
        if "pagekind" not in context:
            context["pagekind"] = ["list", "tags_page"]
        output_name = os.path.join(self.site.config['OUTPUT_FOLDER'], self.site.path('{}_index'.format(taxonomy.classification_name), None, lang))
        task = self.site.generic_post_list_renderer(
            lang,
            [],
            output_name,
            taxonomy.template_for_classification_overview,
            kw['filters'],
            context,
        )
        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.taxonomies:page')]
        task['basename'] = str(self.name)
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
                         feed_url, _enclosure, kw["feed_link_append_query"]))],
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
            return utils.adjust_name_for_index_link(self.site.link(feed.format(kind), classification, lang), i, displayed_i, lang, self.site, force_addition, extension)

        def page_path(i, displayed_i, num_pages, force_addition, extension=None):
            feed = "{}_atom" if extension == ".atom" else "{}"
            return utils.adjust_name_for_index_path(self.site.path(feed.format(kind), classification, lang), i, displayed_i, lang, self.site, force_addition, extension)

        context = copy(context)
        if kw["generate_rss"]:
            # On a tag page, the feeds include the tag's feeds
            rss_link = ("""<link rel="alternate" type="application/rss+xml" title="RSS for {0} {1} ({2})" href="{3}">""".format(
                taxonomy.classification_name, context['classification_title'], lang, self.site.link('{}_rss'.format(kind), classification, lang)))
            context['rss_link'] = rss_link
        if "pagekind" not in context:
            context["pagekind"] = ["index", "tag_page"]
        template_name = taxonomy.template_for_list_of_one_classification

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
        template_name = taxonomy.template_for_list_of_one_classification
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

        if self.site.config['GENERATE_ATOM']:
            yield self._generate_classification_page_as_list_atom(kind, taxonomy, classification, filtered_posts, context, kw, lang)

    def _filter_list(self, post_list, lang):
        """Return only the posts which should be shown for this language."""
        if self.site.config["SHOW_UNTRANSLATED_POSTS"]:
            return post_list
        else:
            return [x for x in post_list if x.is_translation_available(lang)]

    def _generate_classification_page(self, taxonomy, classification, post_list, lang):
        """Render index or post list and associated feeds per classification."""
        # Filter list
        filtered_posts = self._filter_list(post_list, lang)
        if len(filtered_posts) == 0 and taxonomy.omit_empty_classifications:
            return
        # Should we create this list?
        if not taxonomy.should_generate_classification_list(classification, filtered_posts, lang):
            return
        # Get data
        context, kw = taxonomy.provide_context_and_uptodate(classification, lang)
        kw = copy(kw)
        kw['filters'] = self.site.config['FILTERS']
        kw['site_url'] = self.site.config['SITE_URL']
        kw['blog_title'] = self.site.config['BLOG_TITLE']
        kw['generate_rss'] = self.site.config['GENERATE_RSS']
        kw["feed_teasers"] = self.site.config["FEED_TEASERS"]
        kw["feed_plain"] = self.site.config["FEED_PLAIN"]
        kw["feed_link_append_query"] = self.site.config["FEED_LINKS_APPEND_QUERY"]
        kw["feed_length"] = self.site.config['FEED_LENGTH']
        kw["output_folder"] = self.site.config['OUTPUT_FOLDER']
        context = copy(context)
        context["permalink"] = self.site.link(taxonomy.classification_name, classification, lang)
        # Generate RSS feed
        if kw["generate_rss"]:
            yield self._generate_classification_page_as_rss(taxonomy, classification, filtered_posts, context['title'], context.get("description"), kw, lang)
        # Render HTML
        if taxonomy.show_list_as_index:
            yield self._generate_classification_page_as_index(taxonomy, classification, filtered_posts, context, kw, lang)
        else:
            yield self._generate_classification_page_as_list(taxonomy, classification, filtered_posts, context, kw, lang)

    def gen_tasks(self):
        """Render the tag pages and feeds."""
        self.site.scan_posts()
        yield self.group_task()

        for taxonomy in [p.plugin_object for p in self.site.plugin_manager.getPluginsOfCategory('Taxonomy')]:
            # Should this taxonomy be considered after all?
            if not taxonomy.is_enabled():
                continue
            for lang in self.site.config["TRANSLATIONS"]:
                if not taxonomy.is_enabled(lang):
                    continue
                # Generate list of classifications (i.e. classification overview)
                if taxonomy.template_for_classification_overview is not None:
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
