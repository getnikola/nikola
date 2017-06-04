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

"""Registers all default filters."""

from __future__ import unicode_literals, print_function

from nikola.plugin_categories import ConfigPlugin
from nikola import filters


class DefaultFilters(ConfigPlugin):
    """Register all default filters."""

    name = "default_filters"

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        super(DefaultFilters, self).set_site(site)
        # Filter names are registered by formatting them by the following string
        filter_name_format = 'filters.{0}'
        for filter_name, filter_definition in filters.__dict__.items():
            # Ignore objects whose name starts with an underscore, or which are not callable
            if filter_name.startswith('_'):
                continue
            if not callable(filter_definition):
                continue
            # Register all other objects as filters
            site.register_filter(filter_name_format.format(filter_name), filter_definition)
