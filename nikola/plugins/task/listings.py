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

from nikola.plugin_categories import Task
from nikola import utils


class Listings(Task):
    """Render pretty listings."""

    name = "render_listings"

    def set_site(self, site):
        site.register_path_handler('listing', self.listing_path)
        return super(Listings, self).set_site(site)

    def gen_tasks(self):
        """Render pretty code listings."""
        kw = {
            "default_lang": self.site.config["DEFAULT_LANG"],
            "listings_folder": self.site.config["LISTINGS_FOLDER"],
            "output_folder": self.site.config["OUTPUT_FOLDER"],
            "index_file": self.site.config["INDEX_FILE"],
        }

        # Things to ignore in listings
        ignored_extensions = (".pyc", ".pyo")

        def render_listing(in_name, out_name, folders=[], files=[]):
            link_name = ''
            if in_name:
                with open(in_name, 'r') as fd:
                    try:
                        lexer = get_lexer_for_filename(in_name)
                    except:
                        lexer = TextLexer()
                    code = highlight(fd.read(), lexer,
                                     HtmlFormatter(cssclass='code',
                                                   linenos="table", nowrap=False,
                                                   lineanchors=utils.slugify(in_name),
                                                   anchorlinenos=True))
                title = os.path.basename(in_name)
                link_name = in_name
            else:
                code = ''
                title = ''
            crumbs = utils.get_crumbs(os.path.relpath(out_name,
                                                      kw['output_folder']),
                                      is_file=True)
            context = {
                'code': code,
                'title': title,
                'crumbs': crumbs,
                'permalink': self.site.link('listing', link_name),
                'lang': kw['default_lang'],
                'folders': natsort.natsorted(folders),
                'files': natsort.natsorted(files),
                'description': title,
            }
            self.site.render_template('listing.tmpl', out_name,
                                      context)

        yield self.group_task()

        template_deps = self.site.template_system.template_deps('listing.tmpl')
        for root, dirs, files in os.walk(kw['listings_folder'], followlinks=True):
            files = [f for f in files if os.path.splitext(f)[-1] not in ignored_extensions]

            # Render all files
            out_name = os.path.join(
                kw['output_folder'],
                root, kw['index_file']
            )
            yield {
                'basename': self.name,
                'name': out_name,
                'file_dep': template_deps,
                'targets': [out_name],
                'actions': [(render_listing, [None, out_name, dirs, files])],
                # This is necessary to reflect changes in blog title,
                # sidebar links, etc.
                'uptodate': [utils.config_changed({
                    1: self.site.GLOBAL_CONTEXT,
                    2: files,
                    3: dirs
                })],
                'clean': True,
            }
            for f in files:
                ext = os.path.splitext(f)[-1]
                if ext in ignored_extensions:
                    continue
                in_name = os.path.join(root, f)
                out_name = os.path.join(
                    kw['output_folder'],
                    root,
                    f) + '.html'
                yield {
                    'basename': self.name,
                    'name': out_name,
                    'file_dep': template_deps + [in_name],
                    'targets': [out_name],
                    'actions': [(render_listing, [in_name, out_name])],
                    # This is necessary to reflect changes in blog title,
                    # sidebar links, etc.
                    'uptodate': [utils.config_changed(
                        self.site.GLOBAL_CONTEXT)],
                    'clean': True,
                }

    def listing_path(self, name, lang):
        return [_f for _f in [self.site.config['LISTINGS_FOLDER'], name +
                              '.html'] if _f]
