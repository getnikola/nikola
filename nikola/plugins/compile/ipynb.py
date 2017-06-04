# -*- coding: utf-8 -*-

# Copyright © 2013-2017 Damián Avila, Chris Warrick and others.

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

"""Page compiler plugin for nbconvert."""

from __future__ import unicode_literals, print_function
import io
import json
import os
import sys

try:
    from nbconvert.exporters import HTMLExporter
    import nbformat
    current_nbformat = nbformat.current_nbformat
    from jupyter_client import kernelspec
    from traitlets.config import Config
    flag = True
except ImportError:
    flag = None

from nikola import shortcodes as sc
from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing, get_logger, STDERR_HANDLER, LocaleBorg


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

    def _compile_string(self, nb_json):
        """Export notebooks as HTML strings."""
        self._req_missing_ipynb()
        c = Config(self.site.config['IPYNB_CONFIG'])
        c.update(get_default_jupyter_config())
        exportHtml = HTMLExporter(config=c)
        body, _ = exportHtml.from_notebook_node(nb_json)
        return body

    @staticmethod
    def _nbformat_read(in_file):
        return nbformat.read(in_file, current_nbformat)

    def _req_missing_ipynb(self):
        if flag is None:
            req_missing(['notebook>=4.0.0'], 'build this site (compile ipynb)')

    def compile_string(self, data, source_path=None, is_two_file=True, post=None, lang=None):
        """Compile notebooks into HTML strings."""
        new_data, shortcodes = sc.extract_shortcodes(data)
        output = self._compile_string(nbformat.reads(new_data, current_nbformat))
        return self.site.apply_shortcodes_uuid(output, shortcodes, filename=source_path, with_dependencies=True, extra_context=dict(post=post))

    # TODO remove in v8
    def compile_html_string(self, source, is_two_file=True):
        """Export notebooks as HTML strings."""
        with io.open(source, "r", encoding="utf8") as in_file:
            nb_json = nbformat.read(in_file, current_nbformat)
        return self._compile_string(nb_json)

    def compile(self, source, dest, is_two_file=False, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        with io.open(dest, "w+", encoding="utf8") as out_file:
            with io.open(source, "r", encoding="utf8") as in_file:
                nb_str = in_file.read()
            output, shortcode_deps = self.compile_string(nb_str, is_two_file, post, lang)
            out_file.write(output)
        if post is None:
            if shortcode_deps:
                self.logger.error(
                    "Cannot save dependencies for post {0} (post unknown)",
                    source)
        else:
            post._depfile[dest] += shortcode_deps

    def read_metadata(self, post, file_metadata_regexp=None, unslugify_titles=False, lang=None):
        """Read metadata directly from ipynb file.

        As ipynb file support arbitrary metadata as json, the metadata used by Nikola
        will be assume to be in the 'nikola' subfield.
        """
        self._req_missing_ipynb()
        if lang is None:
            lang = LocaleBorg().current_lang
        source = post.translated_source_path(lang)
        with io.open(source, "r", encoding="utf8") as in_file:
            nb_json = nbformat.read(in_file, current_nbformat)
        # Metadata might not exist in two-file posts or in hand-crafted
        # .ipynb files.
        return nb_json.get('metadata', {}).get('nikola', {})

    def create_post(self, path, **kw):
        """Create a new post."""
        self._req_missing_ipynb()
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
            nb = nbformat.v4.new_notebook()
            nb["cells"] = [nbformat.v4.new_markdown_cell(content)]

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
            nbformat.write(nb, fd, 4)


def get_default_jupyter_config():
    """Search default jupyter configuration location paths.

    Return dictionary from configuration json files.
    """
    config = {}
    try:
        from jupyter_core.paths import jupyter_config_path
    except ImportError:
        # jupyter not installed, must be using IPython
        return config

    for parent in jupyter_config_path():
        try:
            for file in os.listdir(parent):
                if 'nbconvert' in file and file.endswith('.json'):
                    abs_path = os.path.join(parent, file)
                    with open(abs_path) as config_file:
                        config.update(json.load(config_file))
        except OSError:
            # some paths jupyter uses to find configurations
            # may not exist
            pass

    return config
