# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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

from __future__ import unicode_literals, print_function

import os

from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
import natsort
import re

from nikola.plugin_categories import Task
from nikola import utils


# FIXME: (almost) duplicated with mdx_nikola.py
CODERE = re.compile('<div class="code"><pre>(.*?)</pre></div>', flags=re.MULTILINE | re.DOTALL)


class Listings(Task):
    """Render pretty listings."""

    name = "render_listings"

    def set_site(self, site):
        site.register_path_handler('listing', self.listing_path)
        return super(Listings, self).set_site(site)

    def register_output_name(self, input_folder, rel_name, rel_output_name):
        if rel_name not in self.improper_input_file_mapping:
            self.improper_input_file_mapping[rel_name] = []
        self.improper_input_file_mapping[rel_name].append(rel_output_name)
        self.proper_input_file_mapping[os.path.join(input_folder, rel_name)] = rel_output_name

    def gen_tasks(self):
        """Render pretty code listings."""
        kw = {
            "default_lang": self.site.config["DEFAULT_LANG"],
            "listings_folders": self.site.config["LISTINGS_FOLDERS"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "index_file": self.site.config["INDEX_FILE"],
            "strip_indexes": self.site.config['STRIP_INDEXES'],
            "filters": self.site.config["FILTERS"],
        }

        # Verify that no folder in LISTINGS_FOLDERS appears twice (neither on input nor output side)
        self.input_folders = list(kw['listings_folders'].items())
        self.output_folders = list(kw['listings_folders'].keys())
        self.input_folders_s = set(kw['listings_folders'].items())
        self.output_folders_s = set(kw['listings_folders'].keys())

        if len(self.input_folders) != len(self.input_folders_s):
            utils.LOGGER.error("A listings input folder was specified multiple times, exiting.")
            exit(1)
        elif len(self.output_folders) != len(self.output_folders_s):
            utils.LOGGER.error("A listings output folder was specified multiple times, exiting.")
            exit(1)

        # Things to ignore in listings
        ignored_extensions = (".pyc", ".pyo")

        def render_listing(in_name, out_name, input_folder, output_folder, folders=[], files=[]):
            if in_name:
                with open(in_name, 'r') as fd:
                    try:
                        lexer = get_lexer_for_filename(in_name)
                    except:
                        lexer = TextLexer()
                    code = highlight(fd.read(), lexer,
                                     HtmlFormatter(cssclass='code',
                                                   linenos="table", nowrap=False,
                                                   lineanchors=utils.slugify(in_name, force=True),
                                                   anchorlinenos=True))
                # the pygments highlighter uses <div class="codehilite"><pre>
                # for code.  We switch it to reST's <pre class="code">.
                code = CODERE.sub('<pre class="code literal-block">\\1</pre>', code)
                title = os.path.basename(in_name)
            else:
                code = ''
                title = os.path.split(os.path.dirname(out_name))[1]
            crumbs = utils.get_crumbs(os.path.relpath(out_name,
                                                      kw['output_folder']),
                                      is_file=True)
            permalink = self.site.link(
                'listing',
                os.path.join(
                    input_folder,
                    os.path.relpath(
                        out_name,
                        os.path.join(
                            kw['output_folder'],
                            output_folder))))
            if self.site.config['COPY_SOURCES']:
                source_link = permalink[:-5]
            else:
                source_link = None
            context = {
                'code': code,
                'title': title,
                'crumbs': crumbs,
                'permalink': permalink,
                'lang': kw['default_lang'],
                'folders': natsort.natsorted(folders),
                'files': natsort.natsorted(files),
                'description': title,
                'source_link': source_link,
            }
            self.site.render_template('listing.tmpl', out_name,
                                      context)

        yield self.group_task()

        self.improper_input_file_mapping = dict()
        self.proper_input_file_mapping = dict()
        # improper_input_file_mapping maps a relative input file (relative to
        # its corresponding input directory) to a list of the output files.
        # Since several input directories can contain files of the same name,
        # a list is needed. This is needed for compatibility to previous Nikola
        # versions, where there was no need to specify the input directory name
        # when asking for a link via site.link('listing', ...).
        template_deps = self.site.template_system.template_deps('listing.tmpl')
        # proper_input_file_mapping maps relative input file (relative to CWD)
        # to a generated output file. Since we don't allow an input directory
        # to appear more than once in LISTINGS_FOLDERS, we can map directly to
        # a file name (and not a list of files).
        for input_folder, output_folder in kw['listings_folders'].items():
            for root, dirs, files in os.walk(input_folder, followlinks=True):
                files = [f for f in files if os.path.splitext(f)[-1] not in ignored_extensions]

                uptodate = {'c': self.site.GLOBAL_CONTEXT}

                for k, v in self.site.GLOBAL_CONTEXT['template_hooks'].items():
                    uptodate['||template_hooks|{0}||'.format(k)] = v._items

                for k in self.site._GLOBAL_CONTEXT_TRANSLATABLE:
                    uptodate[k] = self.site.GLOBAL_CONTEXT[k](kw['default_lang'])

                # save navigation links as dependencies
                uptodate['navigation_links'] = uptodate['c']['navigation_links'](kw['default_lang'])

                uptodate['kw'] = kw

                uptodate2 = uptodate.copy()
                uptodate2['f'] = files
                uptodate2['d'] = dirs

                # Compute relative path; can't use os.path.relpath() here as it
                rel_path = root[len(input_folder):]  # returns "." instead of ""
                if rel_path[:1] == os.sep:
                    rel_path = rel_path[1:]

                # Record file names
                rel_name = os.path.join(rel_path, kw['index_file'])
                rel_output_name = os.path.join(output_folder, rel_path, kw['index_file'])
                self.register_output_name(input_folder, rel_name, rel_output_name)

                # Render all files
                out_name = os.path.join(kw['output_folder'], rel_output_name)
                yield utils.apply_filters({
                    'basename': self.name,
                    'name': out_name,
                    'file_dep': template_deps,
                    'targets': [out_name],
                    'actions': [(render_listing, [None, out_name, input_folder, output_folder, dirs, files])],
                    # This is necessary to reflect changes in blog title,
                    # sidebar links, etc.
                    'uptodate': [utils.config_changed(uptodate2)],
                    'clean': True,
                }, kw["filters"])
                for f in files:
                    ext = os.path.splitext(f)[-1]
                    if ext in ignored_extensions:
                        continue
                    in_name = os.path.join(root, f)
                    # Record file names
                    rel_name = os.path.join(rel_path, f + '.html')
                    rel_output_name = os.path.join(output_folder, rel_path, f + '.html')
                    self.register_output_name(input_folder, rel_name, rel_output_name)
                    # Set up output name
                    out_name = os.path.join(kw['output_folder'], rel_output_name)
                    # Yield task
                    yield utils.apply_filters({
                        'basename': self.name,
                        'name': out_name,
                        'file_dep': template_deps + [in_name],
                        'targets': [out_name],
                        'actions': [(render_listing, [in_name, out_name, input_folder, output_folder])],
                        # This is necessary to reflect changes in blog title,
                        # sidebar links, etc.
                        'uptodate': [utils.config_changed(uptodate)],
                        'clean': True,
                    }, kw["filters"])
                    if self.site.config['COPY_SOURCES']:
                        rel_name = os.path.join(rel_path, f)
                        rel_output_name = os.path.join(output_folder, rel_path, f)
                        self.register_output_name(input_folder, rel_name, rel_output_name)
                        out_name = os.path.join(kw['output_folder'], rel_output_name)
                        yield utils.apply_filters({
                            'basename': self.name,
                            'name': out_name,
                            'file_dep': [in_name],
                            'targets': [out_name],
                            'actions': [(utils.copy_file, [in_name, out_name])],
                            'clean': True,
                        }, kw["filters"])

    def listing_path(self, name, lang):
        name += '.html'
        if name in self.proper_input_file_mapping:
            # If the name shows up in this dict, everything's fine.
            name = self.proper_input_file_mapping[name]
        elif name in self.improper_input_file_mapping:
            # If the name shows up in this dict, we have to check for
            # ambiguities.
            if len(self.improper_input_file_mapping[name]) > 1:
                utils.LOGGER.error("Using non-unique listing name '{0}', which maps to more than one listing name ({1})!".format(name, str(self.improper_input_file_mapping[name])))
                exit(1)
            if len(self.site.config['LISTINGS_FOLDERS']) > 1:
                utils.LOGGER.warn("Using listings names in site.link() without input directory prefix while configuration's LISTINGS_FOLDERS has more than one entries.")
            name = self.improper_input_file_mapping[name][0]
        else:
            utils.LOGGER.error("Unknown listing name {0}!".format(name))
            raise Exception("Unknown listing name {0}!".format(name))
        path_parts = list(os.path.split(name))
        return [_f for _f in path_parts if _f]
