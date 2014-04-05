# -*- coding: utf-8 -*-

# Copyright © 2013-2014 Damián Avila and others.

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
import codecs
import os

try:
    from IPython.nbconvert.exporters import HTMLExporter
    from IPython.nbformat import current as nbformat
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

    def compile_html(self, source, dest, is_two_file=True):
        if flag is None:
            req_missing(['ipython>=1.1.0'], 'build this site (compile ipynb)')
        makedirs(os.path.dirname(dest))
        HTMLExporter.default_template = 'basic'
        c = Config(self.site.config['IPYNB_CONFIG'])
        exportHtml = HTMLExporter(config=c)
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                nb = in_file.read()
                nb_json = nbformat.reads_json(nb)
            (body, resources) = exportHtml.from_notebook_node(nb_json)
            out_file.write(body)

    def create_post(self, path, **kw):
        # content and onefile are ignored by ipynb.
        kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        kw.pop('is_page', False)

        makedirs(os.path.dirname(path))
        if onefile:
            raise Exception('The one-file format is not supported by this compiler.')
        with codecs.open(path, "wb+", "utf8") as fd:
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
