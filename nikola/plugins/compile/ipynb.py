# -*- coding: utf-8 -*-

# Copyright © 2013-2025 Damián Avila, Chris Warrick and others.

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

import json
import os
from pathlib import Path

try:
    import nbconvert
    from nbconvert.exporters import HTMLExporter
    import nbformat
    current_nbformat = nbformat.current_nbformat
    from jupyter_client import kernelspec
    from traitlets.config import Config
    NBCONVERT_VERSION_MAJOR = int(nbconvert.__version__.partition(".")[0])
    flag = True
except ImportError:
    flag = None

from nikola import shortcodes as sc
from nikola.plugin_categories import PageCompiler
from nikola.utils import makedirs, req_missing, LocaleBorg


class CompileIPynb(PageCompiler):
    """Compile IPynb into HTML."""

    name = "ipynb"
    friendly_name = "Jupyter Notebook"
    demote_headers = True
    default_kernel = 'python3'
    supports_metadata = True

    def _compile_string(self, nb_json):
        """Export notebooks as HTML strings."""
        self._req_missing_ipynb()
        c = Config(get_default_jupyter_config())
        c.merge(Config(self.site.config['IPYNB_CONFIG']))
        if 'template_file' not in self.site.config['IPYNB_CONFIG'].get('Exporter', {}):
            if NBCONVERT_VERSION_MAJOR >= 6:
                c['Exporter']['template_file'] = 'classic/base.html.j2'
            else:
                c['Exporter']['template_file'] = 'basic.tpl'  # not a typo
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
        return self.site.apply_shortcodes_uuid(output, shortcodes, filename=source_path, extra_context={'post': post})

    def compile(self, source, dest, is_two_file=False, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        makedirs(os.path.dirname(dest))
        nb_str = Path(source).read_text(encoding="utf-8-sig")
        output, shortcode_deps = self.compile_string(nb_str, source,
                                                     is_two_file, post,
                                                     lang)
        Path(dest).write_text(output, encoding="utf-8")
        if post is None:
            if shortcode_deps:
                self.logger.error(
                    "Cannot save dependencies for post {0} (post unknown)",
                    source)
        else:
            post._depfile[dest] += shortcode_deps

    def read_metadata(self, post, lang=None):
        """Read metadata directly from ipynb file.

        As ipynb files support arbitrary metadata as json, the metadata used by Nikola
        will be assume to be in the 'nikola' subfield.
        """
        self._req_missing_ipynb()
        if lang is None:
            lang = LocaleBorg().current_lang
        source = post.translated_source_path(lang)
        with Path(source).open("r", encoding="utf-8-sig") as in_file:
            nb_json = nbformat.read(in_file, current_nbformat)
        # Metadata might not exist in two-file posts or in hand-crafted
        # .ipynb files.
        return nb_json.get('metadata', {}).get('nikola', {})

    def create_post(self, path, **kw):
        """Create a new post."""
        self._req_missing_ipynb()
        content = kw.pop('content', None)
        onefile = kw.pop('onefile', False)
        kernel = kw.pop('jupyter_kernel', None)
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

            if kernel is None:
                kernel = self.default_kernel
                self.logger.warning('No kernel specified, assuming "{0}".'.format(kernel))

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

        if onefile:
            nb["metadata"]["nikola"] = metadata

        with Path(path).open("w+", encoding="utf-8") as fd:
            nbformat.write(nb, fd, 4)


def get_default_jupyter_config():
    """Search default jupyter configuration location paths.

    Return dictionary from configuration json files.
    """
    config = {}
    from jupyter_core.paths import jupyter_config_path

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
