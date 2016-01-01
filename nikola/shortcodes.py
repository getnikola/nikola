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

"""Support for Hugo-style shortcodes."""

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
    [['foo', ([], {'data': ''}), 0, 11], ['bar', ([], {'data': ''}), 11, 22]]
    >>> pprint.pprint(list(_find_shortcodes('{{% foo bar baz=bat fee=fi fo fum %}}')))
    [['foo',
      (['bar', 'fo', 'fum'], {'baz': 'bat', 'data': '', 'fee': 'fi'}),
      0,
      37]]
    >>> pprint.pprint(list(_find_shortcodes('{{% foo bar bat=baz%}}some data{{% /foo %}}')))
    [['foo', (['bar'], {'bat': 'baz', 'data': 'some data'}), 0, 43]]
    """
    # FIXME: this is really space-intolerant

    pos = 0
    while True:
        start = data.find('{{%', pos)
        if start == -1:
            break
        # Get the whole shortcode tag
        end = data.find('%}}', start + 1)
        name, args = parse_sc(data[start + 3:end].strip())
        # Check if this start has a matching close
        close_tag = '{{% /{} %}}'.format(name)
        close = data.find(close_tag, end + 3)
        if close == -1:  # No closer
            end = end + 3
            args[1]['data'] = ''
        else:  # Tag with closer
            args[1]['data'] = data[end + 3:close - 1]
            end = close + len(close_tag) + 1
        pos = end
        yield [name, args, start, end]


def parse_sc(data):
    """Parse shortcode arguments into a tuple."""
    elements = data.split(' ', 1)
    name = elements[0]
    if len(elements) == 1:
        # No arguments
        return name, ([], {})
    args = []
    kwargs = {}

    # "Simple" argument parser.
    # flag can be one of:
    # 0 name
    # 1 value                               +value
    # 2 name inside quotes                  +quotes
    # 3 value inside quotes
    # 4 [unsupported]                       +backslash
    # 5 value inside backslash
    # 4 [unsupported]
    # 7 value inside quotes and backslash
    flag = 0
    cname = ''
    cvalue = ''
    qc = ''
    for char in elements[1]:
        if flag & 4 and flag & 1:
            # Backslash in value: escape next character, no matter what
            cvalue += char
            flag = flag & 3
        elif flag & 4:
            # Backslash in name: escape next character, no matter what
            cname += char
            flag = flag & 3
        elif char == '=' and flag == 0:
            # Equals sign inside unquoted name: switch to value
            flag = 1
        elif char == ' ' and flag == 0:
            # Space inside unquoted name: save as positional argument
            args.append(cname)
            cname = cvalue = qc = ''
        elif char == ' ' and flag == 1:
            # Space inside unquoted value: save as keyword argument
            kwargs[cname] = cvalue
            flag = 0
            cname = cvalue = qc = ''
        elif char == ' ' and flag == 2:
            # Space inside quoted name: save to name
            cname += char
        elif char == ' ' and flag == 3:
            # Space inside quoted value: save to value
            cvalue += char
        elif char == '\\':
            # Backslash: next character will be escaped
            flag = flag | 4
        elif char == '"' or char == "'":
            # Quote handler
            qc = char
            if not flag & 2:
                flag += 2
            elif flag & 2 and qc == char:
                flag -= 2
            elif flag == 2:
                # Unbalanced quotes, reproduce as is
                cname += char
            elif flag == 3:
                # Unbalanced quotes, reproduce as is
                cvalue += char
        elif flag & 1:
            # Fallback: add anything else to value
            cvalue += char
        else:
            # Fallback: add anything else to name
            cname += char

    # Handle last argument
    if cvalue:
        kwargs[cname] = cvalue
    else:
        args.append(cname)

    return name, (args, kwargs)
