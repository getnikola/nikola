# Copyright (c) 2013 Damian Avila.

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
    from .nbformat import current as nbformat
    from .nbconvert.converters import bloggerhtml as nbconverter
    bloggerhtml = True
except ImportError:
    bloggerhtml = None

from nikola.plugin_categories import PageCompiler


class CompileIPynb(PageCompiler):
    """Compile IPynb into HTML."""

    name = "ipynb"

    def compile_html(self, source, dest, is_two_file=True):
        if bloggerhtml is None:
            raise Exception('To build this site, you also need '
                            'https://github.com/damianavila/com'
                            'pile_ipynb-for-Nikola.git.')
        try:
            os.makedirs(os.path.dirname(dest))
        except:
            pass
        converter = nbconverter.ConverterBloggerHTML()
        with codecs.open(dest, "w+", "utf8") as out_file:
            with codecs.open(source, "r", "utf8") as in_file:
                data = in_file.read()
                converter.nb = nbformat.reads_json(data)
            output = converter.convert()
            out_file.write(output)

    def create_post(self, path, onefile=False, **kw):
        metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)
        d_name = os.path.dirname(path)
        if not os.path.isdir(d_name):
            os.makedirs(os.path.dirname(path))
        meta_path = os.path.join(d_name, kw['slug'] + ".meta")
        with codecs.open(meta_path, "wb+", "utf8") as fd:
            if onefile:
                fd.write('%s\n' % kw['title'])
                fd.write('%s\n' % kw['slug'])
                fd.write('%s\n' % kw['date'])
                fd.write('%s\n' % kw['tags'])
        print("Your post's metadata is at: ", meta_path)
        with codecs.open(path, "wb+", "utf8") as fd:
            fd.write("""{
 "metadata": {
  "name": "%s"
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
}""" % kw['slug'])
