# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys


import io
import shutil
import tempfile
import unittest
from os import path

from nikola.plugins.compile.markdown import CompileMarkdown
from .base import BaseTestCase, FakeSite


class CompileMarkdownTests(BaseTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.input_path = path.join(self.tmp_dir, 'input.markdown')
        self.output_path = path.join(self.tmp_dir, 'output.html')

        self.compiler = CompileMarkdown()
        self.compiler.set_site(FakeSite())

    def compile(self, input_string):
        with io.open(self.input_path, "w+", encoding="utf8") as input_file:
            input_file.write(input_string)

        self.compiler.compile_html(self.input_path, self.output_path)

        output_str = None
        with io.open(self.output_path, "r", encoding="utf8") as output_path:
            output_str = output_path.read()

        return output_str

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_compile_html_empty(self):
        input_str = ''
        actual_output = self.compile(input_str)
        self.assertEquals(actual_output, '')

    def test_compile_html_code_hilite(self):
        input_str = '''\
    #!python
    from this
'''
        expected_output = '''\
<table class="codehilitetable"><tr><td class="linenos">\
<div class="linenodiv"><pre>1</pre></div>\
</td><td class="code"><pre class="code literal-block"><span></span>\
<span class="kn">from</span> <span class="nn">this</span>
</pre>
</td></tr></table>
'''

        actual_output = self.compile(input_str)
        self.assertEquals(actual_output.strip(), expected_output.strip())

    def test_compile_strikethrough(self):
        input_str = '~~striked out text~~'
        expected_output = '<p><del>striked out text</del></p>'

        actual_output = self.compile(input_str)
        self.assertEquals(actual_output.strip(), expected_output.strip())

if __name__ == '__main__':
    unittest.main()
