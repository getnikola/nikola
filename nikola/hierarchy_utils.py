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

"""Hierarchy utility functions."""

import natsort

__all__ = ('TreeNode', 'clone_treenode', 'flatten_tree_structure',
           'sort_classifications', 'join_hierarchical_category_path',
           'parse_escaped_hierarchical_category_name',)


class TreeNode(object):
    """A tree node."""

    indent_levels = None  # use for formatting comments as tree
    indent_change_before = 0  # use for formatting comments as tree
    indent_change_after = 0  # use for formatting comments as tree

    # The indent levels and changes allow to render a tree structure
    # without keeping track of all that information during rendering.
    #
    # The indent_change_before is the different between the current
    # comment's level and the previous comment's level; if the number
    # is positive, the current level is indented further in, and if it
    # is negative, it is indented further out. Positive values can be
    # used to open HTML tags for each opened level.
    #
    # The indent_change_after is the difference between the next
    # comment's level and the current comment's level. Negative values
    # can be used to close HTML tags for each closed level.
    #
    # The indent_levels list contains one entry (index, count) per
    # level, informing about the index of the current comment on that
    # level and the count of comments on that level (before a comment
    # of a higher level comes). This information can be used to render
    # tree indicators, for example to generate a tree such as:
    #
    # +--- [(0,3)]
    # +-+- [(1,3)]
    # | +--- [(1,3), (0,2)]
    # | +-+- [(1,3), (1,2)]
    # |   +--- [(1,3), (1,2), (0, 1)]
    # +-+- [(2,3)]
    #   +- [(2,3), (0,1)]
    #
    # (The lists used as labels represent the content of the
    # indent_levels property for that node.)

    def __init__(self, name, parent=None):
        """Initialize node."""
        self.name = name
        self.parent = parent
        self.children = []

    def get_path(self):
        """Get path."""
        path = []
        curr = self
        while curr is not None:
            path.append(curr)
            curr = curr.parent
        return reversed(path)

    def get_children(self):
        """Get children of a node."""
        return self.children

    def __str__(self):
        """Stringify node (return name)."""
        return self.name

    def _repr_partial(self):
        """Return partial representation."""
        if self.parent:
            return "{0}/{1!r}".format(self.parent._repr_partial(), self.name)
        else:
            return repr(self.name)

    def __repr__(self):
        """Return programmer-friendly node representation."""
        return "<TreeNode {0}>".format(self._repr_partial())


def clone_treenode(treenode, parent=None, acceptor=lambda x: True):
    """Clone a TreeNode.

    Children are only cloned if `acceptor` returns `True` when
    applied on them.

    Returns the cloned node if it has children or if `acceptor`
    applied to it returns `True`. In case neither applies, `None`
    is returned.
    """
    # Copy standard TreeNode stuff
    node_clone = TreeNode(treenode.name, parent)
    node_clone.children = [clone_treenode(node, parent=node_clone, acceptor=acceptor) for node in treenode.children]
    node_clone.children = [node for node in node_clone.children if node]
    node_clone.indent_levels = treenode.indent_levels
    node_clone.indent_change_before = treenode.indent_change_before
    node_clone.indent_change_after = treenode.indent_change_after
    if hasattr(treenode, 'classification_path'):
        # Copy stuff added by taxonomies_classifier plugin
        node_clone.classification_path = treenode.classification_path
        node_clone.classification_name = treenode.classification_name

    # Accept this node if there are no children (left) and acceptor fails
    if not node_clone.children and not acceptor(treenode):
        return None
    return node_clone


def flatten_tree_structure(root_list):
    """Flatten a tree."""
    elements = []

    def generate(input_list, indent_levels_so_far):
        """Generate flat list of nodes."""
        for index, element in enumerate(input_list):
            # add to destination
            elements.append(element)
            # compute and set indent levels
            indent_levels = indent_levels_so_far + [(index, len(input_list))]
            element.indent_levels = indent_levels
            # add children
            children = element.get_children()
            element.children_count = len(children)
            generate(children, indent_levels)

    generate(root_list, [])
    # Add indent change counters
    level = 0
    last_element = None
    for element in elements:
        new_level = len(element.indent_levels)
        # Compute level change before this element
        change = new_level - level
        if last_element is not None:
            last_element.indent_change_after = change
        element.indent_change_before = change
        # Update variables
        level = new_level
        last_element = element
    # Set level change after last element
    if last_element is not None:
        last_element.indent_change_after = -level
    return elements


def parse_escaped_hierarchical_category_name(category_name):
    """Parse a category name."""
    result = []
    current = None
    index = 0
    next_backslash = category_name.find('\\', index)
    next_slash = category_name.find('/', index)
    while index < len(category_name):
        if next_backslash == -1 and next_slash == -1:
            current = (current if current else "") + category_name[index:]
            index = len(category_name)
        elif next_slash >= 0 and (next_backslash == -1 or next_backslash > next_slash):
            result.append((current if current else "") + category_name[index:next_slash])
            current = ''
            index = next_slash + 1
            next_slash = category_name.find('/', index)
        else:
            if len(category_name) == next_backslash + 1:
                raise Exception("Unexpected '\\' in '{0}' at last position!".format(category_name))
            esc_ch = category_name[next_backslash + 1]
            if esc_ch not in {'/', '\\'}:
                raise Exception("Unknown escape sequence '\\{0}' in '{1}'!".format(esc_ch, category_name))
            current = (current if current else "") + category_name[index:next_backslash] + esc_ch
            index = next_backslash + 2
            next_backslash = category_name.find('\\', index)
            if esc_ch == '/':
                next_slash = category_name.find('/', index)
    if current is not None:
        result.append(current)
    return result


def join_hierarchical_category_path(category_path):
    """Join a category path."""
    def escape(s):
        """Espace one part of category path."""
        return s.replace('\\', '\\\\').replace('/', '\\/')

    return '/'.join([escape(p) for p in category_path])


def sort_classifications(taxonomy, classifications, lang):
    """Sort the given list of classifications of the given taxonomy and language.

    ``taxonomy`` must be a ``Taxonomy`` plugin.
    ``classifications`` must be an iterable collection of
    classification strings for that taxonomy.
    ``lang`` is the language the classifications are for.

    The result will be returned as a sorted list. Sorting will
    happen according to the way the complete classification
    hierarchy for the taxonomy is sorted.
    """
    if taxonomy.has_hierarchy:
        # To sort a hierarchy of classifications correctly, we first
        # build a tree out of them (and mark for each node whether it
        # appears in the list), then sort the tree node-wise, and finally
        # collapse the tree into a list of recombined classifications.

        # Step 1: build hierarchy. Here, each node consists of a boolean
        # flag (node appears in list) and a dictionary mapping path elements
        # to nodes.
        root = [False, {}]
        for classification in classifications:
            node = root
            for elt in taxonomy.extract_hierarchy(classification):
                if elt not in node[1]:
                    node[1][elt] = [False, {}]
                node = node[1][elt]
            node[0] = True
        # Step 2: sort hierarchy. The result for a node is a pair
        # (flag, subnodes), where subnodes is a list of pairs (name, subnode).

        def sort_node(node, level=0):
            """Return sorted node, with children as `(name, node)` list instead of a dictionary."""
            keys = natsort.natsorted(node[1].keys(), alg=natsort.ns.F | natsort.ns.IC)
            taxonomy.sort_classifications(keys, lang, level)
            subnodes = []
            for key in keys:
                subnodes.append((key, sort_node(node[1][key], level + 1)))
            return (node[0], subnodes)

        root = sort_node(root)
        # Step 3: collapse the tree structure into a linear sorted list,
        # with a node coming before its children.

        def append_node(classifications, node, path=()):
            """Append the node and then its children to the classifications list."""
            if node[0]:
                classifications.append(taxonomy.recombine_classification_from_hierarchy(path))
            for key, subnode in node[1]:
                append_node(classifications, subnode, path + (key, ))

        classifications = []
        append_node(classifications, root)
        return classifications
    else:
        # Sorting a flat hierarchy is simpler. We pre-sort with
        # natsorted and call taxonomy.sort_classifications.
        classifications = natsort.natsorted(classifications, alg=natsort.ns.F | natsort.ns.IC)
        taxonomy.sort_classifications(classifications, lang)
        return classifications
