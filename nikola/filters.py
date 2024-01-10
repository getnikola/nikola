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

"""Utility functions to help run filters on files.

All filters defined in this module are registered in Nikola.__init__.
"""

import io
import json
import os
import re
import shutil
import shlex
import subprocess
import tempfile
from functools import wraps

import lxml
import requests

from .utils import req_missing, LOGGER, slugify

try:
    import typogrify.filters as typo
except ImportError:
    typo = None


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
    def f_in_file(fname, *args, **kwargs):
        with open(fname, 'rb') as inf:
            data = inf.read()
        data = f(data, *args, **kwargs)
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
    def f_in_file(fname, *args, **kwargs):
        with io.open(fname, 'r', encoding='utf-8-sig') as inf:
            data = inf.read()
        data = f(data, *args, **kwargs)
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
            subprocess.call('yui-compressor', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            yuicompressor = 'yui-compressor'
        except Exception:
            pass
    if not yuicompressor:
        try:
            subprocess.call('yuicompressor', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            yuicompressor = 'yuicompressor'
        except Exception:
            raise Exception("yui-compressor is not installed.")
            return False

    return runinplace('{} --nomunge %1 -o %2'.format(yuicompressor), infile)


@_ConfigurableFilter(executable='CLOSURE_COMPILER_EXECUTABLE')
def closure_compiler(infile, executable='closure-compiler'):
    """Run closure-compiler on a file."""
    return runinplace('{} --warning_level QUIET --js %1 --js_output_file %2'.format(executable), infile)


@_ConfigurableFilter(executable='OPTIPNG_EXECUTABLE')
def optipng(infile, executable='optipng'):
    """Run optipng on a file."""
    return runinplace("{} -preserve -o2 -quiet %1".format(executable), infile)


@_ConfigurableFilter(executable='JPEGOPTIM_EXECUTABLE')
def jpegoptim(infile, executable='jpegoptim'):
    """Run jpegoptim on a file."""
    return runinplace("{} -p --strip-all -q %1".format(executable), infile)


@_ConfigurableFilter(executable='JPEGOPTIM_EXECUTABLE')
def jpegoptim_progressive(infile, executable='jpegoptim'):
    """Run jpegoptim on a file and convert to progressive."""
    return runinplace("{} -p --strip-all --all-progressive -q %1".format(executable), infile)


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


def _run_typogrify(data, typogrify_filters, ignore_tags=None):
    """Run typogrify with ignore support."""
    default_ignore_tags = ["title", ".math"]
    if ignore_tags is None:
        ignore_tags = default_ignore_tags
    else:
        ignore_tags = ignore_tags + default_ignore_tags

    data = _normalize_html(data)

    section_list = typo.process_ignores(data, ignore_tags)

    rendered_text = ""
    for text_item, should_process in section_list:
        if should_process:
            for f in typogrify_filters:
                text_item = f(text_item)

        rendered_text += text_item

    return rendered_text


@apply_to_text_file
def typogrify(data):
    """Prettify text with typogrify."""
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify filter', optional=True)
        return data
    return _run_typogrify(data, [typo.amp, typo.widont, typo.smartypants, typo.caps, typo.initial_quotes])


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

    return _run_typogrify(data, [typo.amp, typo.widont, _smarty_oldschool, typo.smartypants, typo.caps, typo.initial_quotes])


@apply_to_text_file
def typogrify_sans_widont(data):
    """Prettify text with typogrify, skipping the widont filter."""
    # typogrify with widont disabled because it caused broken headline
    # wrapping, see issue #1465
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify_sans_widont filter')
        return data

    return _run_typogrify(data, [typo.amp, typo.smartypants, typo.caps, typo.initial_quotes])


@apply_to_text_file
def typogrify_custom(data, typogrify_filters=None, ignore_tags=None):
    """Run typogrify with a custom list of filter functions."""
    if typo is None:
        req_missing(['typogrify'], 'use the typogrify filter', optional=True)
        return data
    if typogrify_filters is None:
        typogrify_filters = [typo.amp, typo.widont, typo.smartypants, typo.caps, typo.initial_quotes]
    return _run_typogrify(data, typogrify_filters, ignore_tags)


@apply_to_text_file
def php_template_injection(data):
    """Insert PHP code into Nikola templates."""
    template = re.search(r'<\!-- __NIKOLA_PHP_TEMPLATE_INJECTION source\:(.*) checksum\:(.*)__ -->', data)
    if template:
        source = template.group(1)
        with io.open(source, "r", encoding="utf-8-sig") as in_file:
            phpdata = in_file.read()
        _META_SEPARATOR = '(' + os.linesep * 2 + '|' + ('\n' * 2) + '|' + ("\r\n" * 2) + ')'
        phpdata = re.split(_META_SEPARATOR, phpdata, maxsplit=1)[-1]
        phpdata = data.replace(template.group(0), phpdata)
        return phpdata
    else:
        return data


@apply_to_text_file
def cssminify(data):
    """Minify CSS using <https://www.toptal.com/developers/cssminifier>."""
    try:
        url = 'https://www.toptal.com/developers/cssminifier/api/raw'
        _data = {'input': data}
        response = requests.post(url, data=_data)
        if response.status_code != 200:
            LOGGER.error("Can't use toptal.com CSS Minifier: HTTP status {}", response.status_code)
            return data
        return response.text
    except Exception as exc:
        LOGGER.error("Can't use toptal.com CSS Minifier: {}", exc)
        return data


@apply_to_text_file
def jsminify(data):
    """Minify JS using <https://www.toptal.com/developers/javascript-minifier>."""
    try:
        url = 'https://www.toptal.com/developers/javascript-minifier/api/raw'
        _data = {'input': data}
        response = requests.post(url, data=_data)
        if response.status_code != 200:
            LOGGER.error("Can't use toptal.com JavaScript Minifier: HTTP status {}", response.status_code)
            return data
        return response.text
    except Exception as exc:
        LOGGER.error("Can't use toptal.com JavaScript Minifier: {}", exc)
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
    except Exception:
        pass
    return '<!DOCTYPE html>\n' + data


# The function is used in other filters, so the decorator cannot be used directly.
normalize_html = apply_to_text_file(_normalize_html)


@_ConfigurableFilter(xpath_list='HEADER_PERMALINKS_XPATH_LIST', file_blacklist='HEADER_PERMALINKS_FILE_BLACKLIST')
def add_header_permalinks(fname, xpath_list=None, file_blacklist=None):
    """Post-process HTML via lxml to add header permalinks Sphinx-style."""
    # Blacklist requires custom file handling
    file_blacklist = file_blacklist or []
    if fname in file_blacklist:
        return
    with io.open(fname, 'r', encoding='utf-8-sig') as inf:
        data = inf.read()
    doc = lxml.html.document_fromstring(data)
    # Get language for slugify
    try:
        lang = doc.attrib['lang']  # <html lang="…">
    except KeyError:
        # Circular import workaround (utils imports filters)
        from nikola.utils import LocaleBorg
        lang = LocaleBorg().current_lang

    xpath_set = set()
    if not xpath_list:
        xpath_list = ['*//div[@class="e-content entry-content"]//{hx}']
    for xpath_expr in xpath_list:
        for hx in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            xpath_set.add(xpath_expr.format(hx=hx))
    for x in xpath_set:
        nodes = doc.findall(x)
        for node in nodes:
            parent = node.getparent()
            if 'id' in node.attrib:
                hid = node.attrib['id']
            elif 'id' in parent.attrib:
                # docutils: <div> has an ID and contains the header
                hid = parent.attrib['id']
            else:
                # Using force-mode, because not every character can appear in a
                # HTML id
                node.attrib['id'] = slugify(node.text_content(), lang, True)
                hid = node.attrib['id']

            new_node = lxml.html.fragment_fromstring('<a href="#{0}" class="headerlink" title="Permalink to this heading">¶</a>'.format(hid))
            node.append(new_node)

    with io.open(fname, 'w', encoding='utf-8') as outf:
        outf.write('<!DOCTYPE html>\n' + lxml.html.tostring(doc, encoding="unicode"))


@_ConfigurableFilter(top_classes='DEDUPLICATE_IDS_TOP_CLASSES')
@apply_to_text_file
def deduplicate_ids(data, top_classes=None):
    """Post-process HTML via lxml to deduplicate IDs."""
    if not top_classes:
        top_classes = ('postpage', 'storypage')
    doc = lxml.html.document_fromstring(data)
    elements = doc.xpath('//*')
    all_ids = [element.attrib.get('id') for element in elements]
    seen_ids = set()
    duplicated_ids = set()
    for i in all_ids:
        if i is not None and i in seen_ids:
            duplicated_ids.add(i)
        else:
            seen_ids.add(i)

    if duplicated_ids:
        # Well, that sucks.
        for i in duplicated_ids:
            # Results are ordered the same way they are ordered in document
            offending_elements = doc.xpath('//*[@id="{}"]'.format(i))
            counter = 2
            # If this is a story or a post, do it from top to bottom, because
            # updates to those are more likely to appear at the bottom of pages.
            # For anything else, including indexes, do it from bottom to top,
            # because new posts appear at the top of pages.
            # We also leave the first result out, so there is one element with
            # "plain" ID
            if any(doc.find_class(c) for c in top_classes):
                off = offending_elements[1:]
            else:
                off = offending_elements[-2::-1]
            for e in off:
                new_id = i
                while new_id in seen_ids:
                    new_id = '{0}-{1}'.format(i, counter)
                    counter += 1
                e.attrib['id'] = new_id
                seen_ids.add(new_id)
                # Find headerlinks that we can fix.
                headerlinks = e.find_class('headerlink')
                for hl in headerlinks:
                    # We might get headerlinks of child elements
                    if hl.attrib['href'] == '#' + i:
                        hl.attrib['href'] = '#' + new_id
                        break
        return '<!DOCTYPE html>\n' + lxml.html.tostring(doc, encoding='unicode')
    else:
        return data
