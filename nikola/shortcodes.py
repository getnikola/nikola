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

"""Support for Hugo-style shortcodes."""

from __future__ import unicode_literals

import uuid

from .utils import LOGGER
import sys


class ParsingError(Exception):
    """Used for forwarding parsing error messages to apply_shortcodes."""

    pass


def _format_position(data, pos):
    """Return position formatted as line/column.

    This is used for prettier error messages.
    """
    line = 0
    col = 0
    llb = ''  # last line break
    for c in data[:pos]:
        if c == '\r' or c == '\n':
            if llb and c != llb:
                llb = ''
            else:
                line += 1
                col = 0
                llb = c
        else:
            col += 1
            llb = ''
    return "line {0}, column {1}".format(line + 1, col + 1)


def _skip_whitespace(data, pos, must_be_nontrivial=False):
    """Return first position after whitespace.

    If must_be_nontrivial is set to True, raises ParsingError
    if no whitespace is found.
    """
    if must_be_nontrivial:
        if pos == len(data) or not data[pos].isspace():
            raise ParsingError("Expecting whitespace at {0}!".format(_format_position(data, pos)))
    while pos < len(data):
        if not data[pos].isspace():
            break
        pos += 1
    return pos


def _skip_nonwhitespace(data, pos):
    """Return first position not before pos which contains a non-whitespace character."""
    for i, x in enumerate(data[pos:]):
        if x.isspace():
            return pos + i
    return len(data)


def _parse_quoted_string(data, start):
    """Parse a quoted string starting at position start in data.

    Returns the position after the string followed by the string itself.
    """
    value = ''
    qc = data[start]
    pos = start + 1
    while pos < len(data):
        char = data[pos]
        if char == '\\':
            if pos + 1 < len(data):
                value += data[pos + 1]
                pos += 2
            else:
                raise ParsingError("Unexpected end of data while escaping ({0})".format(_format_position(data, pos)))
        elif (char == "'" or char == '"') and char == qc:
            return pos + 1, value
        else:
            value += char
            pos += 1
    raise ParsingError("Unexpected end of unquoted string (started at {0})!".format(_format_position(data, start)))


def _parse_unquoted_string(data, start, stop_at_equals):
    """Parse an unquoted string starting at position start in data.

    Returns the position after the string followed by the string itself.
    In case stop_at_equals is set to True, an equal sign will terminate
    the string.
    """
    value = ''
    pos = start
    while pos < len(data):
        char = data[pos]
        if char == '\\':
            if pos + 1 < len(data):
                value += data[pos + 1]
                pos += 2
            else:
                raise ParsingError("Unexpected end of data while escaping ({0})".format(_format_position(data, pos)))
        elif char.isspace():
            break
        elif char == '=' and stop_at_equals:
            break
        elif char == "'" or char == '"':
            raise ParsingError("Unexpected quotation mark in unquoted string ({0})".format(_format_position(data, pos)))
        else:
            value += char
            pos += 1
    return pos, value


def _parse_string(data, start, stop_at_equals=False, must_have_content=False):
    """Parse a string starting at position start in data.

    Returns the position after the string, followed by the string itself, and
    followed by a flog indicating whether the following character is an equals
    sign (only set if stop_at_equals is True).

    If must_have_content is set to True, no empty unquoted strings are accepted.
    """
    if start == len(data):
        raise ParsingError("Expecting string, but found end of input!")
    char = data[start]
    if char == '"' or char == "'":
        end, value = _parse_quoted_string(data, start)
        has_content = True
    else:
        end, value = _parse_unquoted_string(data, start, stop_at_equals)
        has_content = len(value) > 0
    if must_have_content and not has_content:
        raise ParsingError("String starting at {0} must be non-empty!".format(_format_position(data, start)))

    next_is_equals = False
    if stop_at_equals and end + 1 < len(data):
        next_is_equals = (data[end] == '=')
    return end, value, next_is_equals


def _parse_shortcode_args(data, start, shortcode_name, start_pos):
    """When pointed to after a shortcode's name in a shortcode tag, parses the shortcode's arguments until '%}}'.

    Returns the position after '%}}', followed by a tuple (args, kw).

    name and start_pos are only used for formatting error messages.
    """
    args = []
    kwargs = {}

    pos = start
    while True:
        # Skip whitespaces
        try:
            pos = _skip_whitespace(data, pos, must_be_nontrivial=True)
        except ParsingError:
            if not args and not kwargs:
                raise ParsingError("Shortcode '{0}' starting at {1} is not terminated correctly with '%}}}}'!".format(shortcode_name, _format_position(data, start_pos)))
            else:
                raise ParsingError("Syntax error in shortcode '{0}' at {1}: expecting whitespace!".format(shortcode_name, _format_position(data, pos)))
        if pos == len(data):
            break
        # Check for end of shortcode
        if pos + 3 <= len(data) and data[pos:pos + 3] == '%}}':
            return pos + 3, (args, kwargs)
        # Read name
        pos, name, next_is_equals = _parse_string(data, pos, stop_at_equals=True, must_have_content=True)
        if next_is_equals:
            # Read value
            pos, value, _ = _parse_string(data, pos + 1, stop_at_equals=False, must_have_content=False)
            # Store keyword argument
            kwargs[name] = value
        else:
            # Store positional argument
            args.append(name)

    raise ParsingError("Shortcode '{0}' starting at {1} is not terminated correctly with '%}}}}'!".format(shortcode_name, _format_position(data, start_pos)))


def _new_sc_id():
    return str('SHORTCODE{0}REPLACEMENT'.format(str(uuid.uuid4()).replace('-', '')))


def extract_shortcodes(data):
    """
    Return data with replaced shortcodes, shortcodes.

    data is the original data, with the shortcodes replaced by UUIDs.

    a dictionary of shortcodes, where the keys are UUIDs and the values
    are the shortcodes themselves ready to process.
    """
    shortcodes = {}
    splitted = _split_shortcodes(data)

    if not data:  # Empty
        return '', {}

    def extract_data_chunk(data):
        """Take a list of splitted shortcodes and return a string and a tail.

        The string is data, the tail is ready for a new run of this same function.
        """
        text = []
        for i, token in enumerate(data):
            if token[0] == 'SHORTCODE_START':
                name = token[3]
                sc_id = _new_sc_id()
                text.append(sc_id)
                # See if this shortcode closes
                for j in range(i, len(data)):
                    if data[j][0] == 'SHORTCODE_END' and data[j][3] == name:
                        # Extract this chunk
                        shortcodes[sc_id] = ''.join(t[1] for t in data[i:j + 1])
                        return ''.join(text), data[j + 1:]
                # Doesn't close
                shortcodes[sc_id] = token[1]
                return ''.join(text), data[i + 1:]
            elif token[0] == 'TEXT':
                text.append(token[1])
                return ''.join(text), data[1:]
            elif token[0] == 'SHORTCODE_END':  # This is malformed
                raise Exception('Closing unopened shortcode {}'.format(token[3]))

    text = []
    tail = splitted
    while True:
        new_text, tail = extract_data_chunk(tail)
        text.append(new_text)
        if not tail:
            break
    return ''.join(text), shortcodes


def _split_shortcodes(data):
    """Given input data, splits it into a sequence of texts, shortcode starts and shortcode ends.

    Returns a list of tuples of the following forms:

        1. ("TEXT", text)
        2. ("SHORTCODE_START", text, start, name, args)
        3. ("SHORTCODE_END", text, start, name)

    Here, text is the raw text represented by the token; start is the starting position in data
    of the token; name is the name of the shortcode; and args is a tuple (args, kw) as returned
    by _parse_shortcode_args.
    """
    pos = 0
    result = []
    while pos < len(data):
        # Search for shortcode start
        start = data.find('{{%', pos)
        if start < 0:
            result.append(("TEXT", data[pos:]))
            break
        result.append(("TEXT", data[pos:start]))
        # Extract name
        name_start = _skip_whitespace(data, start + 3)
        name_end = _skip_nonwhitespace(data, name_start)
        name = data[name_start:name_end]
        if not name:
            raise ParsingError("Syntax error: '{{{{%' must be followed by shortcode name ({0})!".format(_format_position(data, start)))
        # Finish shortcode
        if name[0] == '/':
            # This is a closing shortcode
            name = name[1:]
            end_start = _skip_whitespace(data, name_end)  # start of '%}}'
            pos = end_start + 3
            # Must be followed by '%}}'
            if pos > len(data) or data[end_start:pos] != '%}}':
                raise ParsingError("Syntax error: '{{{{% /{0}' must be followed by ' %}}}}' ({1})!".format(name, _format_position(data, end_start)))
            result.append(("SHORTCODE_END", data[start:pos], start, name))
        elif name == '%}}':
            raise ParsingError("Syntax error: '{{{{%' must be followed by shortcode name ({0})!".format(_format_position(data, start)))
        else:
            # This is an opening shortcode
            pos, args = _parse_shortcode_args(data, name_end, shortcode_name=name, start_pos=start)
            result.append(("SHORTCODE_START", data[start:pos], start, name, args))
    return result


# FIXME: in v8, get rid of with_dependencies
def apply_shortcodes(data, registry, site=None, filename=None, raise_exceptions=False, lang=None, with_dependencies=False, extra_context={}):
    """Apply Hugo-style shortcodes on data.

    {{% name parameters %}} will end up calling the registered "name" function with the given parameters.
    {{% name parameters %}} something {{% /name %}} will call name with the parameters and
    one extra "data" parameter containing " something ".

    If raise_exceptions is set to True, instead of printing error messages and terminating, errors are
    passed on as exceptions to the caller.

    The site parameter is passed with the same name to the shortcodes so they can access Nikola state.

    >>> print(apply_shortcodes('==> {{% foo bar=baz %}} <==', {'foo': lambda *a, **k: k['bar']}))
    ==> baz <==
    >>> print(apply_shortcodes('==> {{% foo bar=baz %}}some data{{% /foo %}} <==', {'foo': lambda *a, **k: k['bar']+k['data']}))
    ==> bazsome data <==
    """
    empty_string = data[:0]  # same string type as data; to make Python 2 happy
    try:
        # Split input data into text, shortcodes and shortcode endings
        sc_data = _split_shortcodes(data)
        # Now process data
        result = []
        dependencies = []
        pos = 0
        while pos < len(sc_data):
            current = sc_data[pos]
            if current[0] == "TEXT":
                result.append(current[1])
                pos += 1
            elif current[0] == "SHORTCODE_END":
                raise ParsingError("Found shortcode ending '{{{{% /{0} %}}}}' which isn't closing a started shortcode ({1})!".format(current[3], _format_position(data, current[2])))
            elif current[0] == "SHORTCODE_START":
                name = current[3]
                # Check if we can find corresponding ending
                found = None
                for p in range(pos + 1, len(sc_data)):
                    if sc_data[p][0] == "SHORTCODE_END" and sc_data[p][3] == name:
                        found = p
                        break
                if found:
                    # Found ending. Extract data argument:
                    data_arg = []
                    for p in range(pos + 1, found):
                        data_arg.append(sc_data[p][1])
                    data_arg = empty_string.join(data_arg)
                    pos = found + 1
                else:
                    # Single shortcode
                    pos += 1
                    data_arg = ''
                args, kw = current[4]
                kw['site'] = site
                kw['data'] = data_arg
                kw['lang'] = lang
                kw.update(extra_context)
                if name in registry:
                    f = registry[name]
                    if getattr(f, 'nikola_shortcode_pass_filename', None):
                        kw['filename'] = filename
                    res = f(*args, **kw)
                    if not isinstance(res, tuple):  # For backards compatibility
                        res = (res, [])
                else:
                    LOGGER.error('Unknown shortcode {0} (started at {1})', name, _format_position(data, current[2]))
                    res = ('', [])
                result.append(res[0])
                dependencies += res[1]
        if with_dependencies:
            return empty_string.join(result), dependencies
        return empty_string.join(result)
    except ParsingError as e:
        if raise_exceptions:
            # Throw up
            raise
        if filename:
            LOGGER.error("Shortcode error in file {0}: {1}".format(filename, e))
        else:
            LOGGER.error("Shortcode error: {0}".format(e))
        sys.exit(1)
