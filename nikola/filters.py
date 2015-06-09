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

"""Utility functions to help you run filters on files."""

from .utils import req_missing
from functools import wraps
import os
import io
import shutil
import subprocess
import tempfile
import shlex

try:
    import typogrify.filters as typo
except ImportError:
    typo = None  # NOQA


def apply_to_binary_file(f):
    """Take a function f that transforms a data argument, and returns
    a function that takes a filename and applies f to the contents,
    in place.  Reads files in binary mode."""
    @wraps(f)
    def f_in_file(fname):
        with open(fname, 'rb') as inf:
            data = inf.read()
        data = f(data)
        with open(fname, 'wb+') as outf:
            outf.write(data)

    return f_in_file


def apply_to_text_file(f):
    """Take a function f that transforms a data argument, and returns
    a function that takes a filename and applies f to the contents,
    in place.  Reads files in UTF-8."""
    @wraps(f)
    def f_in_file(fname):
        with io.open(fname, 'r', encoding='utf-8') as inf:
            data = inf.read()
        data = f(data)
        with io.open(fname, 'w+', encoding='utf-8') as outf:
            outf.write(data)

    return f_in_file


def list_replace(the_list, find, replacement):
    "Replace all occurrences of ``find`` with ``replacement`` in ``the_list``"
    for i, v in enumerate(the_list):
        if v == find:
            the_list[i] = replacement


def runinplace(command, infile):
    """Run a command in-place on a file.

    command is a string of the form: "commandname %1 %2" and
    it will be execed with infile as %1 and a temporary file
    as %2. Then, that temporary file will be moved over %1.

    Example usage:

    runinplace("yui-compressor %1 -o %2", "myfile.css")

    That will replace myfile.css with a minified version.

    You can also supply command as a list.
    """

    if not isinstance(command, list):
        command = shlex.split(command)

    tmpdir = None

    if "%2" in command:
        tmpdir = tempfile.mkdtemp(prefix="nikola")
        tmpfname = os.path.join(tmpdir, os.path.basename(infile))

    try:
        list_replace(command, "%1", infile)
        if tmpdir:
            list_replace(command, "%2", tmpfname)

        subprocess.check_call(command)

        if tmpdir:
            shutil.move(tmpfname, infile)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)


def yui_compressor(infile):
    yuicompressor = False
    try:
        subprocess.call('yui-compressor', stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        yuicompressor = 'yui-compressor'
    except Exception:
        pass
    if not yuicompressor:
        try:
            subprocess.call('yuicompressor', stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
            yuicompressor = 'yuicompressor'
        except:
            raise Exception("yui-compressor is not installed.")
            return False

    return runinplace(r'{} --nomunge %1 -o %2'.format(yuicompressor), infile)


def closure_compiler(infile):
    return runinplace(r'closure-compiler --warning_level QUIET --js %1 --js_output_file %2', infile)


def optipng(infile):
    return runinplace(r"optipng -preserve -o2 -quiet %1", infile)


def jpegoptim(infile):
    return runinplace(r"jpegoptim -p --strip-all -q %1", infile)


def html_tidy_nowrap(infile):
    return _html_tidy_runner(infile, r"-quiet --show-info no --show-warnings no -utf8 -indent --indent-attributes no --sort-attributes alpha --wrap 0 --wrap-sections no --tidy-mark no -modify %1")


def html_tidy_wrap(infile):
    return _html_tidy_runner(infile, r"-quiet --show-info no --show-warnings no -utf8 -indent --indent-attributes no --sort-attributes alpha --wrap 80 --wrap-sections no --tidy-mark no -modify %1")


def html_tidy_wrap_attr(infile):
    return _html_tidy_runner(infile, r"-quiet --show-info no --show-warnings no -utf8 -indent --indent-attributes yes --sort-attributes alpha --wrap 80 --wrap-sections no --tidy-mark no -modify %1")


def html_tidy_mini(infile):
    return _html_tidy_runner(infile, r"-quiet --show-info no --show-warnings no -utf8 --indent-attributes no --sort-attributes alpha --wrap 0 --wrap-sections no --tidy-mark no -modify %1")


def _html_tidy_runner(infile, options):
    """ Warnings (returncode 1) are not critical, and *everything* is a warning """
    try:
        status = runinplace(r"tidy5 " + options, infile)
    except subprocess.CalledProcessError as err:
        status = 0 if err.returncode == 1 else err.returncode
    return status


@apply_to_text_file
def html5lib_minify(data):
    import html5lib
    import html5lib.serializer
    data = html5lib.serializer.serialize(html5lib.parse(data, treebuilder='lxml'),
                                         tree='lxml',
                                         quote_attr_values=False,
                                         omit_optional_tags=True,
                                         minimize_boolean_attributes=True,
                                         strip_whitespace=True,
                                         alphabetical_attributes=True,
                                         escape_lt_in_attrs=True)
    return data


@apply_to_text_file
def html5lib_xmllike(data):
    import html5lib
    import html5lib.serializer
    data = html5lib.serializer.serialize(html5lib.parse(data, treebuilder='lxml'),
                                         tree='lxml',
                                         quote_attr_values=True,
                                         omit_optional_tags=False,
                                         strip_whitespace=False,
                                         alphabetical_attributes=True,
                                         escape_lt_in_attrs=True)
    return data


@apply_to_text_file
def minify_lines(data):
    return data


@apply_to_text_file
def typogrify(data):
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify filter')

    data = typo.amp(data)
    data = typo.widont(data)
    data = typo.smartypants(data)
    # Disabled because of typogrify bug where it breaks <title>
    # data = typo.caps(data)
    data = typo.initial_quotes(data)
    return data


@apply_to_text_file
def typogrify_sans_widont(data):
    # typogrify with widont disabled because it caused broken headline
    # wrapping, see issue #1465
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify_sans_widont filter')

    data = typo.amp(data)
    data = typo.smartypants(data)
    # Disabled because of typogrify bug where it breaks <title>
    # data = typo.caps(data)
    data = typo.initial_quotes(data)
    return data


@apply_to_text_file
def php_template_injection(data):
    import re
    template = re.search('<\!-- __NIKOLA_PHP_TEMPLATE_INJECTION source\:(.*) checksum\:(.*)__ -->', data)
    if template:
        source = template.group(1)
        with io.open(source, "r", encoding="utf-8") as in_file:
            phpdata = in_file.read()
        _META_SEPARATOR = '(' + os.linesep * 2 + '|' + ('\n' * 2) + '|' + ("\r\n" * 2) + ')'
        phpdata = re.split(_META_SEPARATOR, phpdata, maxsplit=1)[-1]
        phpdata = re.sub(template.group(0), phpdata, data)
        return phpdata
    else:
        return data
