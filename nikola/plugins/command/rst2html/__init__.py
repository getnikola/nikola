# -*- coding: utf-8 -*-

# Copyright © 2015-2024 Chris Warrick and others.

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

"""Compile reStructuredText to HTML, using Nikola architecture."""


import io
import lxml.html
from pkg_resources import resource_filename
from mako.template import Template
from nikola.plugin_categories import Command


class CommandRst2Html(Command):
    """Compile reStructuredText to HTML, using Nikola architecture."""

    name = "rst2html"
    doc_usage = "infile"
    doc_purpose = "compile reStructuredText to HTML files"
    needs_config = False

    def _execute(self, options, args):
        """Compile reStructuredText to standalone HTML files."""
        compiler = self.site.plugin_manager.get_plugin_by_name('rest', 'PageCompiler').plugin_object
        if len(args) != 1:
            print("This command takes only one argument (input file name).")
            return 2
        source = args[0]
        with io.open(source, "r", encoding="utf-8-sig") as in_file:
            data = in_file.read()
            output, error_level, deps, shortcode_deps = compiler.compile_string(data, source, True)

        rstcss_path = resource_filename('nikola', 'data/themes/base/assets/css/rst_base.css')
        with io.open(rstcss_path, "r", encoding="utf-8-sig") as fh:
            rstcss = fh.read()

        template_path = resource_filename('nikola', 'plugins/command/rst2html/rst2html.tmpl')
        template = Template(filename=template_path)
        template_output = template.render(rstcss=rstcss, output=output)
        parser = lxml.html.HTMLParser(remove_blank_text=True)
        doc = lxml.html.document_fromstring(template_output, parser)
        html = b'<!DOCTYPE html>\n' + lxml.html.tostring(doc, encoding='utf8', method='html', pretty_print=True)
        print(html.decode('utf-8'))
        if error_level < 3:
            return 0
        else:
            return 1
