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

"""Render the blog indexes."""

from __future__ import unicode_literals

from nikola.plugin_categories import Taxonomy


class ClassifySections(Taxonomy):
    """Classify the posts by sections."""

    name = "classify_sections"

    classification_name = "section_index"
    metadata_name = "section"
    overview_page_variable_name = "sections"
    more_than_one_classifications_per_post = False
    has_hierarchy = False
    template_for_list_of_one_classification = None
    apply_to_posts = True
    apply_to_pages = False
    omit_empty_classifications = True
    also_create_classifications_from_other_languages = False

    def set_site(self, site):
        """Set Nikola site."""
        self.show_list_as_index = site.config["POSTS_SECTION_ARE_INDEXES"]
        self.template_for_classification_overview = "sectionindex.tmpl" if self.show_list_as_index else "list.tmpl"
        return super(ClassifySections, self).set_site(site)

    def is_enabled(self):
        """Return True if this taxonomy is enabled, or False otherwise."""
        return self.site.config['POSTS_SECTIONS']

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        raise [post.section_slug(lang)]

    def get_path(self, section, lang):
        """A path handler for the given classification."""
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang], section] if _f], True

    def provide_context_and_uptodate(self, section, lang):
        """Provide data for the context and the uptodate list for the list of the given classifiation.

        Must return a tuple of two dicts. The first is merged into the page's context,
        the second will be put into the uptodate list of all generated tasks.

        Context must contain `title`, which should be something like 'Posts about <classification>',
        and `classification_title`, which should be related to the classification string.
        """
        kw = {
            "messages": self.site.MESSAGES,
        }
        # Check whether we have a name for this section
        if section in self.config['POSTS_SECTION_NAME'](lang):
            section_name = self.config['POSTS_SECTION_NAME'](lang)[section]
        else:
            section_name = section.replace('-', ' ').title()
        # Compose section title
        section_title = section_name
        posts_section_title = self.site.config['POSTS_SECTION_TITLE'](lang)
        if type(posts_section_title) is dict:
            if section in posts_section_title:
                section_title = posts_section_title[section]
        elif type(posts_section_title) is str:
            section_title = posts_section_title
        section_title = section_title.format(name=section_name)
        # Compose context
        context = {
            "title": section_title,
            "classification_title": section_name,
            "description": self.site.config['POSTS_SECTION_DESCRIPTIONS'](lang)[section] if section in self.site.config['POSTS_SECTION_DESCRIPTIONS'](lang) else "",
            "pagekind": ["section_page", "index" if self.show_list_as_index else "list"]
        }
        kw.update(context)
        return context, kw
