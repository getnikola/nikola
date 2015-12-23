# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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

"""Support for Hugo-style shortcodes."""

try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser

from .utils import LOGGER


def apply_shortcodes(data, registry, site=None):
    """Apply Hugo-style shortcodes on data.

    {{% name parameters %}} will end up calling the registered "name" function with the given parameters.
    {{% name parameters %}} something {{% /name %}} will call name with the parameters and
    one extra "data" parameter containing " something ".

    The site parameter is passed with the same name to the shortcodes so they can access Nikola state.

    >>> apply_shortcodes('==> {{% foo bar=baz %}} <==', {'foo': lambda *a, **k: k['bar']})
    '==> baz <=='
    >>> apply_shortcodes('==> {{% foo bar=baz %}}some data{{% /foo %}} <==', {'foo': lambda *a, **k: k['bar']+k['data']})
    '==> bazsome data <=='
    """
    shortcodes = list(_find_shortcodes(data))
    # Calculate shortcode results
    for sc in shortcodes:
        name, args, start, end = sc
        a, kw = args
        kw['site'] = site
        if name in registry:
            result = registry[name](*a, **kw)
        else:
            LOGGER.error('Unknown shortcode: {}', name)
            result = ''
        sc.append(result)

    # Replace all shortcodes with their output
    for sc in shortcodes[::-1]:
        _, _, start, end, result = sc
        data = data[:start] + result + data[end:]
    return data


def _find_shortcodes(data):
    """Find start and end of shortcode markers.

    >>> import pprint  # (dict sorting for doctest)
    >>> list(_find_shortcodes('{{% foo %}}{{% bar %}}'))
    [['foo', ([], {}), 0, 11], ['bar', ([], {}), 11, 22]]
    >>> pprint.pprint(list(_find_shortcodes('{{% foo bar baz=bat fee=fi fo fum %}}')))
    [['foo', (['bar', 'fo', 'fum'], {'baz': 'bat', 'fee': 'fi'}), 0, 37]]
    >>> pprint.pprint(list(_find_shortcodes('{{% foo bar bat=baz%}}some data{{% /foo %}}')))
    [['foo', (['bar'], {'bat': 'baz', 'data': 'some data'}), 0, 43]]
    """
    # FIXME: this is really space-intolerant

    parser = SCParser()
    pos = 0
    while True:
        start = data.find('{{%', pos)
        if start == -1:
            break
        # Get the whole shortcode tag
        end = data.find('%}}', start + 1)
        name, args = parser.parse_sc('<{}>'.format(data[start + 3:end].strip()))
        # Check if this start has a matching close
        close_tag = '{{% /{} %}}'.format(name)
        close = data.find(close_tag, end + 3)
        if close == -1:  # No closer
            end = end + 3
        else:  # Tag with closer
            args[1]['data'] = data[end + 3:close - 1]
            end = close + len(close_tag) + 1
        pos = end
        yield [name, args, start, end]


class SCParser(HTMLParser):
    """Parser for shortcode arguments."""

    # Because shortcode attributes are HTML-like, we are abusing the HTML parser.
    # TODO replace with self-contained parser
    # FIXME should be able to take quoted positional arguments!

    def parse_sc(self, data):
        """Parse shortcode arguments into a tuple."""
        self.name = None
        self.attrs = {}
        self.feed(data)
        args = []
        kwargs = {}
        for a, b in self.attrs:
            if b is None:
                args.append(a)
            else:
                kwargs[a] = b
        return self.name, (args, kwargs)

    def handle_starttag(self, tag, attrs):
        """Set start tag information on parser object."""
        self.name = tag
        self.attrs = attrs
