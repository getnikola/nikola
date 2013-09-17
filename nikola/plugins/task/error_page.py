# -*- coding: utf-8 -*-

# Copyright © 2012-2013 Roberto Alsina and others.

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

import codecs
import os

from nikola.plugin_categories import Task
from nikola import utils


class ErrorPage(Task):
    """ Create error page into output. """

    name = "error_page"

    def gen_tasks(self):
        """ Generate task for error page tasks."""

        kw = {
            'error_page': self.site.config['CREATE_ERROR_PAGE'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
        }

        if not kw['error_page']:
            # Create a dummy task if no error page needs to be created
            yield {
                'basename': self.name,
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }

        else:
            template_name = '404.tmpl'
            dst = os.path.join(kw["output_folder"], '404.html')
            context = {}
            context["title"] = self.site.MESSAGES[self.site.current_lang()]['Page not found']
            context["description"] = self.site.config['BLOG_DESCRIPTION']
            context["lang"] = self.site.current_lang()

            yield {
                'basename': self.name,
                'name': dst,
                'targets': [dst],
                'actions': [(self.site.render_template, (template_name, dst, context))],
                'clean': True,
                'uptodate': [utils.config_changed(kw)],
            }
