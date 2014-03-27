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

from __future__ import unicode_literals

import codecs
import json
import os

from nikola.plugin_categories import Task
from nikola.utils import (
    config_changed, copy_file, LocaleBorg, makedirs, unicode_str,
)


class Mustache(Task):
    """Render the blog posts as JSON data."""

    name = "render_mustache"

    def gen_tasks(self):
        self.site.scan_posts()

        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "index_display_post_count":
            self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "messages": self.site.MESSAGES,
            "index_teasers": self.site.config['INDEX_TEASERS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "blog_title": self.site.config['BLOG_TITLE'],
            "content_footer": self.site.config['CONTENT_FOOTER'],
        }

        # TODO: timeline is global, get rid of it
        posts = [x for x in self.site.timeline if x.use_in_feeds]
        if not posts:
            yield {
                'basename': 'render_mustache',
                'actions': [],
            }
            return

        def write_file(path, post, lang):

            # Prev/Next links
            prev_link = False
            if post.prev_post:
                prev_link = post.prev_post.permalink(lang).replace(".html",
                                                                   ".json")
            next_link = False
            if post.next_post:
                next_link = post.next_post.permalink(lang).replace(".html",
                                                                   ".json")
            data = {}

            # Configuration
            for k, v in self.site.config.items():
                if isinstance(v, (str, unicode_str)):  # NOQA
                    data[k] = v

            # Tag data
            tags = []
            for tag in post.tags:
                tags.append({'name': tag, 'link': self.site.link("tag", tag,
                                                                 lang)})
            data.update({
                "tags": tags,
                "tags?": True if tags else False,
            })

            # Template strings
            for k, v in kw["messages"][lang].items():
                data["message_" + k] = v

            # Post data
            data.update({
                "title": post.title(lang),
                "text": post.text(lang),
                "prev": prev_link,
                "next": next_link,
                "date":
                post.date.strftime(self.site.GLOBAL_CONTEXT['date_format']),
            })

            # Comments
            context = dict(post=post, lang=LocaleBorg().current_lang)
            context.update(self.site.GLOBAL_CONTEXT)
            data["comment_html"] = self.site.template_system.render_template(
                'mustache-comment-form.tmpl', None, context).strip()

            # Post translations
            translations = []
            for langname in kw["translations"]:
                if langname == lang:
                    continue
                translations.append({'name':
                                     kw["messages"][langname]["Read in English"],
                                    'link': "javascript:load_data('%s');" % post.permalink(langname).replace(".html", ".json")
                                     })
            data["translations"] = translations

            makedirs(os.path.dirname(path))
            with codecs.open(path, 'wb+', 'utf8') as fd:
                fd.write(json.dumps(data))

        for lang in kw["translations"]:
            for i, post in enumerate(posts):
                out_path = post.destination_path(lang, ".json")
                out_file = os.path.join(kw['output_folder'], out_path)
                task = {
                    'basename': 'render_mustache',
                    'name': out_file,
                    'file_dep': post.fragment_deps(lang),
                    'targets': [out_file],
                    'actions': [(write_file, (out_file, post, lang))],
                    'task_dep': ['render_posts'],
                    'uptodate': [config_changed({
                        1: post.text(lang),
                        2: post.prev_post,
                        3: post.next_post,
                        4: post.title(lang),
                    })]
                }
                yield task

        if posts:
            first_post_data = posts[0].permalink(
                self.site.config["DEFAULT_LANG"]).replace(".html", ".json")

        # Copy mustache template
        src = os.path.join(os.path.dirname(__file__), 'mustache-template.html')
        dst = os.path.join(kw['output_folder'], 'mustache-template.html')
        yield {
            'basename': 'render_mustache',
            'name': dst,
            'targets': [dst],
            'file_dep': [src],
            'actions': [(copy_file, (src, dst))],
        }

        # Copy mustache.html with the right starting file in it
        src = os.path.join(os.path.dirname(__file__), 'mustache.html')
        dst = os.path.join(kw['output_folder'], 'mustache.html')

        def copy_mustache():
            with codecs.open(src, 'rb', 'utf8') as in_file:
                with codecs.open(dst, 'wb+', 'utf8') as out_file:
                    data = in_file.read().replace('{{first_post_data}}',
                                                  first_post_data)
                    out_file.write(data)
        yield {
            'basename': 'render_mustache',
            'name': dst,
            'targets': [dst],
            'file_dep': [src],
            'uptodate': [config_changed({1: first_post_data})],
            'actions': [(copy_mustache, [])],
        }
