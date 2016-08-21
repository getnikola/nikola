# -*- coding: utf-8 -*-

# Copyright © 2013-2016 Damián Avila, Chris Warrick and others.

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
import sys

try:
    from nbconvert.exporters import HTMLExporter
    import nbformat
    current_nbformat = nbformat.current_nbformat
    from jupyter_client import kernelspec
    from traitlets.config import Config
    flag = True
    ipy_modern = True
except ImportError:
    try:
        import IPython
        from IPython.nbconvert.exporters import HTMLExporter
        if IPython.version_info[0] >= 3:     # API changed with 3.0.0
            from IPython import nbformat
            current_nbformat = nbformat.current_nbformat
            from IPython.kernel import kernelspec
            ipy_modern = True
        else:
            import IPython.nbformat.current as nbformat
            current_nbformat = 'json'
            kernelspec = None
            ipy_modern = False

        from IPython.config import Config
        flag = True
    except ImportError:
        flag = None
        ipy_modern = None

from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing, get_logger, STDERR_HANDLER


class CompileIPynb(PageCompiler):
    """Compile IPynb into HTML."""

    name = "ipynb"
    friendly_name = "Jupyter/IPython Notebook"
    demote_headers = True
    default_kernel = 'python2' if sys.version_info[0] == 2 else 'python3'

    def set_site(self, site):
        """Set Nikola site."""
        self.logger = get_logger('compile_ipynb', STDERR_HANDLER)
        super(CompileIPynb, self).set_site(site)

    def compile_html_string(self, source, is_two_file=True):
        """Export notebooks as HTML strings."""
        if flag is None:
            req_missing(['ipython[notebook]>=2.0.0'], 'build this site (compile ipynb)')
        c = Config(self.site.config['IPYNB_CONFIG'])
        exportHtml = HTMLExporter(config=c)
        with io.open(source, "r", encoding="utf8") as in_file:
            nb_json = nbformat.read(in_file, current_nbformat)
        (body, resources) = exportHtml.from_notebook_node(nb_json)
        return body

    def compile_html(self, source, dest, is_two_file=True):
        """Compile source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        try:
            post = self.site.post_per_input_file[source]
        except KeyError:
            post = None
        with io.open(dest, "w+", encoding="utf8") as out_file:
            output = self.compile_html_string(source, is_two_file)
            output, shortcode_deps = self.site.apply_shortcodes(output, filename=source, with_dependencies=True, extra_context=dict(post=post))
            out_file.write(output)
        if post is None:
            if shortcode_deps:
                self.logger.error(
                    "Cannot save dependencies for post {0} due to unregistered source file name",
                    source)
        else:
            post._depfile[dest] += shortcode_deps

    def read_metadata(self, post, file_metadata_regexp=None, unslugify_titles=False, lang=None):
        """Read metadata directly from ipynb file.

        As ipynb file support arbitrary metadata as json, the metadata used by Nikola
        will be assume to be in the 'nikola' subfield.
        """
        if flag is None:
            req_missing(['ipython[notebook]>=2.0.0'], 'build this site (compile ipynb)')
        source = post.source_path
        with io.open(source, "r", encoding="utf8") as in_file:
            nb_json = nbformat.read(in_file, current_nbformat)
        # Metadata might not exist in two-file posts or in hand-crafted
        # .ipynb files.
        return nb_json.get('metadata', {}).get('nikola', {})

    def create_post(self, path, **kw):
        """Create a new post."""
        if flag is None:
            req_missing(['ipython[notebook]>=2.0.0'], 'build this site (compile ipynb)')
        content = kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        kernel = kw.pop('ipython_kernel', None)
        # is_page is not needed to create the file
        kw.pop('is_page', False)

        metadata = {}
        metadata.update(self.default_metadata)
        metadata.update(kw)

        makedirs(os.path.dirname(path))

        if content.startswith("{"):
            # imported .ipynb file, guaranteed to start with "{" because it’s JSON.
            nb = nbformat.reads(content, current_nbformat)
        else:
            if ipy_modern:
                nb = nbformat.v4.new_notebook()
                nb["cells"] = [nbformat.v4.new_markdown_cell(content)]
            else:
                nb = nbformat.new_notebook()
                nb["worksheets"] = [nbformat.new_worksheet(cells=[nbformat.new_text_cell('markdown', [content])])]

            if kernelspec is not None:
                if kernel is None:
                    kernel = self.default_kernel
                    self.logger.notice('No kernel specified, assuming "{0}".'.format(kernel))

                IPYNB_KERNELS = {}
                ksm = kernelspec.KernelSpecManager()
                for k in ksm.find_kernel_specs():
                    IPYNB_KERNELS[k] = ksm.get_kernel_spec(k).to_dict()
                    IPYNB_KERNELS[k]['name'] = k
                    del IPYNB_KERNELS[k]['argv']

                if kernel not in IPYNB_KERNELS:
                    self.logger.error('Unknown kernel "{0}". Maybe you mispelled it?'.format(kernel))
                    self.logger.info("Available kernels: {0}".format(", ".join(sorted(IPYNB_KERNELS))))
                    raise Exception('Unknown kernel "{0}"'.format(kernel))

                nb["metadata"]["kernelspec"] = IPYNB_KERNELS[kernel]
            else:
                # Older IPython versions don’t need kernelspecs.
                pass

        if onefile:
            nb["metadata"]["nikola"] = metadata

        with io.open(path, "w+", encoding="utf8") as fd:
            if ipy_modern:
                nbformat.write(nb, fd, 4)
            else:
                nbformat.write(nb, fd, 'ipynb')
