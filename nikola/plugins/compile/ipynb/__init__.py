# -*- coding: utf-8 -*-

# Copyright © 2013-2015 Damián Avila and others.

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

"""Implementation of compile_html based on nbconvert."""

from __future__ import unicode_literals, print_function
import io
import os

try:
    import IPython
    from IPython.nbconvert.exporters import HTMLExporter
    if IPython.version_info[0] >= 3:     # API changed with 3.0.0
        from IPython import nbformat
        current_nbformat = nbformat.current_nbformat
    else:
        import IPython.nbformat.current as nbformat
        current_nbformat = 'json'

    from IPython.config import Config
    flag = True
except ImportError:
    flag = None

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing


class CompileIPynb(PageCompiler):
    """Compile IPynb into HTML."""

    name = "ipynb"
    supports_onefile = False
    demote_headers = True

    def compile_html(self, source, dest, is_two_file=True):
        if flag is None:
            req_missing(['ipython>=1.1.0'], 'build this site (compile ipynb)')
        makedirs(os.path.dirname(dest))
        HTMLExporter.default_template = 'basic'
        c = Config(self.site.config['IPYNB_CONFIG'])
        exportHtml = HTMLExporter(config=c)
        with io.open(dest, "w+", encoding="utf8") as out_file:
            with io.open(source, "r", encoding="utf8") as in_file:
                nb_json = nbformat.read(in_file, current_nbformat)
            (body, resources) = exportHtml.from_notebook_node(nb_json)
            out_file.write(body)

    def read_metadata(self, post, file_metadata_regexp=None, unslugify_titles=False, lang=None):
        """read metadata directly from ipynb file.

        As ipynb file support arbitrary metadata as json, the metadata used by Nikola
        will be assume to be in the 'nikola' subfield.
        """
        source = post.source_path
        with io.open(source, "r", encoding="utf8") as in_file:
            nb_json = nbformat.read(in_file, current_nbformat)
        # metadata should always exist, but we never know if
        # the user crafted the ipynb by hand and did not add it.
        return nb_json.get('metadata', {}).get('nikola', {})

    def create_post(self, path, **kw):
        content = kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        # is_page is not needed to create the file
        kw.pop('is_page', False)

        makedirs(os.path.dirname(path))
        if onefile:
            raise Exception('The one-file format is not supported by this compiler.')
        with io.open(path, "w+", encoding="utf8") as fd:
            if not content.startswith("Write your"):
                fd.write(content)
            else:
                fd.write("""{
 "metadata": {
  "name": ""
 },
 "nbformat": 3,
 "nbformat_minor": 0,
 "worksheets": [
  {
   "cells": [
    {
     "cell_type": "code",
     "collapsed": false,
     "input": [],
     "language": "python",
     "metadata": {},
     "outputs": []
    }
   ],
   "metadata": {}
  }
 ]
}""")
