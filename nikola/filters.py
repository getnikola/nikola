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

"""Utility functions to help run filters on files."""

from functools import wraps
import os
import io
import json
import shutil
import subprocess
import tempfile
import shlex

import lxml
try:
    import typogrify.filters as typo
except ImportError:
    typo = None  # NOQA
import requests

from .utils import req_missing, LOGGER


class _ConfigurableFilter(object):
    """Allow Nikola to configure filter with site's config."""

    def __init__(self, **configuration_variables):
        """Define which arguments to configure from which configuration variables."""
        self.configuration_variables = configuration_variables

    def __call__(self, f):
        """Store configuration_variables as attribute of function."""
        f.configuration_variables = self.configuration_variables
        return f


def apply_to_binary_file(f):
    """Apply a filter to a binary file.

    Take a function f that transforms a data argument, and returns
    a function that takes a filename and applies f to the contents,
    in place.  Reads files in binary mode.
    """
    @wraps(f)
    def f_in_file(fname):
        with open(fname, 'rb') as inf:
            data = inf.read()
        data = f(data)
        with open(fname, 'wb+') as outf:
            outf.write(data)

    return f_in_file


def apply_to_text_file(f):
    """Apply a filter to a text file.

    Take a function f that transforms a data argument, and returns
    a function that takes a filename and applies f to the contents,
    in place.  Reads files in UTF-8.
    """
    @wraps(f)
    def f_in_file(fname):
        with io.open(fname, 'r', encoding='utf-8') as inf:
            data = inf.read()
        data = f(data)
        with io.open(fname, 'w+', encoding='utf-8') as outf:
            outf.write(data)

    return f_in_file


def list_replace(the_list, find, replacement):
    """Replace all occurrences of ``find`` with ``replacement`` in ``the_list``."""
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


@_ConfigurableFilter(executable='YUI_COMPRESSOR_EXECUTABLE')
def yui_compressor(infile, executable=None):
    """Run YUI Compressor on a file."""
    yuicompressor = executable
    if not yuicompressor:
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

    return runinplace('{} --nomunge %1 -o %2'.format(yuicompressor), infile)


@_ConfigurableFilter(executable='CLOSURE_COMPILER_EXECUTABLE')
def closure_compiler(infile, executable='closure-compiler'):
    """Run closure-compiler on a file."""
    return runinplace('{} --warning_level QUIET --js %1 --js_output_file %2'.format(executable), infile)


@_ConfigurableFilter(executable='OPTIPNG_EXECUTABLE')
def optipng(infile, executable='optiong'):
    """Run optipng on a file."""
    return runinplace("{} -preserve -o2 -quiet %1".format(executable), infile)


@_ConfigurableFilter(executable='JPEGOPTIM_EXECUTABLE')
def jpegoptim(infile, executable='jpegoptim'):
    """Run jpegoptim on a file."""
    return runinplace("{} -p --strip-all -q %1".format(executable), infile)


@_ConfigurableFilter(executable='HTML_TIDY_EXECUTABLE')
def html_tidy_withconfig(infile, executable='tidy5'):
    """Run HTML Tidy with tidy5.conf as config file."""
    return _html_tidy_runner(infile, "-quiet --show-info no --show-warnings no -utf8 -indent -config tidy5.conf -modify %1", executable=executable)


@_ConfigurableFilter(executable='HTML_TIDY_EXECUTABLE')
def html_tidy_nowrap(infile, executable='tidy5'):
    """Run HTML Tidy without line wrapping."""
    return _html_tidy_runner(infile, "-quiet --show-info no --show-warnings no -utf8 -indent --indent-attributes no --sort-attributes alpha --wrap 0 --wrap-sections no --drop-empty-elements no --tidy-mark no -modify %1", executable=executable)


@_ConfigurableFilter(executable='HTML_TIDY_EXECUTABLE')
def html_tidy_wrap(infile, executable='tidy5'):
    """Run HTML Tidy with line wrapping."""
    return _html_tidy_runner(infile, "-quiet --show-info no --show-warnings no -utf8 -indent --indent-attributes no --sort-attributes alpha --wrap 80 --wrap-sections no --drop-empty-elements no --tidy-mark no -modify %1", executable=executable)


@_ConfigurableFilter(executable='HTML_TIDY_EXECUTABLE')
def html_tidy_wrap_attr(infile, executable='tidy5'):
    """Run HTML tidy with line wrapping and attribute indentation."""
    return _html_tidy_runner(infile, "-quiet --show-info no --show-warnings no -utf8 -indent --indent-attributes yes --sort-attributes alpha --wrap 80 --wrap-sections no --drop-empty-elements no --tidy-mark no -modify %1", executable=executable)


@_ConfigurableFilter(executable='HTML_TIDY_EXECUTABLE')
def html_tidy_mini(infile, executable='tidy5'):
    """Run HTML tidy with minimal settings."""
    return _html_tidy_runner(infile, "-quiet --show-info no --show-warnings no -utf8 --indent-attributes no --sort-attributes alpha --wrap 0 --wrap-sections no --tidy-mark no --drop-empty-elements no -modify %1", executable=executable)


def _html_tidy_runner(infile, options, executable='tidy5'):
    """Run HTML Tidy."""
    # Warnings (returncode 1) are not critical, and *everything* is a warning.
    try:
        status = runinplace(executable + " " + options, infile)
    except subprocess.CalledProcessError as err:
        status = 0 if err.returncode == 1 else err.returncode
    return status


@apply_to_text_file
def html5lib_minify(data):
    """Minify with html5lib."""
    import html5lib
    import html5lib.serializer
    data = html5lib.serializer.serialize(html5lib.parse(data, treebuilder='lxml'),
                                         tree='lxml',
                                         quote_attr_values='spec',
                                         omit_optional_tags=True,
                                         minimize_boolean_attributes=True,
                                         strip_whitespace=True,
                                         alphabetical_attributes=True,
                                         escape_lt_in_attrs=True)
    return data


@apply_to_text_file
def html5lib_xmllike(data):
    """Transform document to an XML-like form with html5lib."""
    import html5lib
    import html5lib.serializer
    data = html5lib.serializer.serialize(html5lib.parse(data, treebuilder='lxml'),
                                         tree='lxml',
                                         quote_attr_values='always',
                                         omit_optional_tags=False,
                                         strip_whitespace=False,
                                         alphabetical_attributes=True,
                                         escape_lt_in_attrs=True)
    return data


@apply_to_text_file
def minify_lines(data):
    """Do nothing -- deprecated filter."""
    return data


@apply_to_text_file
def typogrify(data):
    """Prettify text with typogrify."""
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify filter', optional=True)
        return data

    data = _normalize_html(data)
    data = typo.amp(data)
    data = typo.widont(data)
    data = typo.smartypants(data)
    # Disabled because of typogrify bug where it breaks <title>
    # data = typo.caps(data)
    data = typo.initial_quotes(data)
    return data


def _smarty_oldschool(text):
    try:
        import smartypants
    except ImportError:
        raise typo.TypogrifyError("Error in {% smartypants %} filter: The Python smartypants library isn't installed.")
    else:
        output = smartypants.convert_dashes_oldschool(text)
        return output


@apply_to_text_file
def typogrify_oldschool(data):
    """Prettify text with typogrify."""
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify_oldschool filter', optional=True)
        return data

    data = _normalize_html(data)
    data = typo.amp(data)
    data = typo.widont(data)
    data = _smarty_oldschool(data)
    data = typo.smartypants(data)
    # Disabled because of typogrify bug where it breaks <title>
    # data = typo.caps(data)
    data = typo.initial_quotes(data)
    return data


@apply_to_text_file
def typogrify_sans_widont(data):
    """Prettify text with typogrify, skipping the widont filter."""
    # typogrify with widont disabled because it caused broken headline
    # wrapping, see issue #1465
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify_sans_widont filter')

    data = _normalize_html(data)
    data = typo.amp(data)
    data = typo.smartypants(data)
    # Disabled because of typogrify bug where it breaks <title>
    # data = typo.caps(data)
    data = typo.initial_quotes(data)
    return data


@apply_to_text_file
def php_template_injection(data):
    """Insert PHP code into Nikola templates."""
    import re
    template = re.search('<\!-- __NIKOLA_PHP_TEMPLATE_INJECTION source\:(.*) checksum\:(.*)__ -->', data)
    if template:
        source = template.group(1)
        with io.open(source, "r", encoding="utf-8") as in_file:
            phpdata = in_file.read()
        _META_SEPARATOR = '(' + os.linesep * 2 + '|' + ('\n' * 2) + '|' + ("\r\n" * 2) + ')'
        phpdata = re.split(_META_SEPARATOR, phpdata, maxsplit=1)[-1]
        phpdata = data.replace(template.group(0), phpdata)
        return phpdata
    else:
        return data


@apply_to_text_file
def cssminify(data):
    """Minify CSS using http://cssminifier.com/."""
    try:
        url = 'http://cssminifier.com/raw'
        _data = {'input': data}
        response = requests.post(url, data=_data)
        if response.status_code != 200:
            LOGGER.error("can't use cssminifier.com: HTTP status {}", response.status_code)
            return data
        return response.text
    except Exception as exc:
        LOGGER.error("can't use cssminifier.com: {}", exc)
        return data


@apply_to_text_file
def jsminify(data):
    """Minify JS using http://javascript-minifier.com/."""
    try:
        url = 'http://javascript-minifier.com/raw'
        _data = {'input': data}
        response = requests.post(url, data=_data)
        if response.status_code != 200:
            LOGGER.error("can't use javascript-minifier.com: HTTP status {}", response.status_code)
            return data
        return response.text
    except Exception as exc:
        LOGGER.error("can't use javascript-minifier.com: {}", exc)
        return data


@apply_to_text_file
def jsonminify(data):
    """Minify JSON files (strip whitespace and use minimal separators)."""
    data = json.dumps(json.loads(data), indent=None, separators=(',', ':'))
    return data


@apply_to_binary_file
def xmlminify(data):
    """Minify XML files (strip whitespace and use minimal separators)."""
    parser = lxml.etree.XMLParser(remove_blank_text=True)
    newdata = lxml.etree.XML(data, parser=parser)
    return lxml.etree.tostring(newdata, encoding='utf-8', method='xml', xml_declaration=True)


def _normalize_html(data):
    """Pass HTML through LXML to clean it up, if possible."""
    try:
        data = lxml.html.tostring(lxml.html.fromstring(data), encoding='unicode')
    except:
        pass
    return '<!DOCTYPE html>\n' + data


normalize_html = apply_to_text_file(_normalize_html)
