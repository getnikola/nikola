# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import shutil
import tempfile
import unittest
from os import path

from nikola.plugins.compile_markdown import CompileMarkdown


class FakeSite(object):
    config = {
        "MARKDOWN_EXTENSIONS": ['fenced_code', 'codehilite']
    }


class CompileMarkdownTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.input_path = path.join(self.tmp_dir, 'input.markdown')
        self.output_path = path.join(self.tmp_dir, 'output.html')

        self.compiler = CompileMarkdown()
        self.compiler.set_site(FakeSite())

    def compile(self, input_string):
        with codecs.open(self.input_path, "w+", "utf8") as input_file:
            input_file.write(input_string)

        self.compiler.compile_html(self.input_path, self.output_path)

        output_str = None
        with codecs.open(self.output_path, "r", "utf8") as output_path:
            output_str = output_path.read()

        return output_str

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_compile_html_empty(self):
        input_str = ''
        actual_output = self.compile(input_str)
        self.assertEquals(actual_output, '')

    def test_compile_html_heading_tags(self):
        input_str = '''\
# header 1
## header 2
### header 3
#### header 4
##### header 5
###### header 6
'''
        expected_output = '''\
<h2>header 1</h2>
<h3>header 2</h3>
<h4>header 3</h4>
<h5>header 4</h5>
<h6>header 5</h6>
<h7>header 6</h7>
'''

        actual_output = self.compile(input_str)
        self.assertEquals(actual_output.strip(), expected_output.strip())

    def test_compile_html_code_hilite(self):
        input_str = '''\
    #!python
    from this
'''
        expected_output = '''\
<table class="codehilitetable"><tr><td class="linenos">\
<div class="linenodiv"><pre>1</pre></div>\
</td><td class="code"><div class="code">\
<pre><span class="kn">from</span> <span class="nn">this</span>
</pre></div>
</td></tr></table>
'''

        actual_output = self.compile(input_str)
        self.assertEquals(actual_output.strip(), expected_output.strip())

    def test_compile_html_gist(self):
        input_str = '''\
Here's a gist file inline:
[:gist: 4747847 zen.py]

Cool, eh?
'''
        expected_output = '''\
<p>Here's a gist file inline:
<div class="gist">
<script src="https://gist.github.com/4747847.js?file=zen.py"></script>
<noscript>
<pre>import this</pre>
</noscript>
</div>
</p>
<p>Cool, eh?</p>
'''
        actual_output = self.compile(input_str)
        self.assertEquals(actual_output.strip(), expected_output.strip())

    def test_compile_html_gist_2(self):
        input_str = '''\
Here's a gist file inline, using reStructuredText syntax:
..gist:: 4747847 zen.py

Cool, eh?
'''
        expected_output = '''\
<p>Here's a gist file inline, using reStructuredText syntax:
<div class="gist">
<script src="https://gist.github.com/4747847.js?file=zen.py"></script>
<noscript>
<pre>import this</pre>
</noscript>
</div>
</p>
<p>Cool, eh?</p>
'''
        actual_output = self.compile(input_str)
        self.assertEquals(actual_output.strip(), expected_output.strip())


if __name__ == '__main__':
    unittest.main()
