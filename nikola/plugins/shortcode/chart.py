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
"""Chart shortcode."""

from ast import literal_eval

from nikola.plugin_categories import ShortcodePlugin
from nikola.utils import req_missing, load_data

try:
    import pygal
except ImportError:
    pygal = None

_site = None


class ChartShortcode(ShortcodePlugin):
    """Plugin for chart shortcode."""

    name = "chart"

    def handler(self, chart_type, **_options):
        """Generate chart using Pygal."""
        if pygal is None:
            msg = req_missing(
                ['pygal'], 'use the Chart directive', optional=True)
            return '<div class="text-error">{0}</div>'.format(msg)
        options = {}
        chart_data = []
        _options.pop('post', None)
        _options.pop('site')
        data = _options.pop('data')

        for line in data.splitlines():
            line = line.strip()
            if line:
                chart_data.append(literal_eval('({0})'.format(line)))
        if 'data_file' in _options:
            options = load_data(_options['data_file'])
            _options.pop('data_file')
            if not chart_data:  # If there is data in the document, it wins
                for k, v in options.pop('data', {}).items():
                    chart_data.append((k, v))

        options.update(_options)

        style_name = options.pop('style', 'BlueStyle')
        if '(' in style_name:  # Parametric style
            style = eval('pygal.style.' + style_name)
        else:
            style = getattr(pygal.style, style_name)
        for k, v in options.items():
            try:
                options[k] = literal_eval(v)
            except Exception:
                options[k] = v
        chart = pygal
        for o in chart_type.split('.'):
            chart = getattr(chart, o)
        chart = chart(style=style)
        if _site and _site.invariant:
            chart.no_prefix = True
        chart.config(**options)
        for label, series in chart_data:
            chart.add(label, series)
        return chart.render().decode('utf8')
