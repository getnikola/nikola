# Copyright (c) 2012 Roberto Alsina y otros.

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
import codecs
import datetime
import os
import sys

from nikola.plugin_categories import Command
from nikola import utils


def filter_post_pages(compiler, is_post, post_compilers, post_pages):
    """Given a compiler ("markdown", "rest"), and whether it's meant for
    a post or a page, and post_compilers, return the correct entry from
    post_pages."""

    # First throw away all the post_pages with the wrong is_post
    filtered = [entry for entry in post_pages if entry[3] == is_post]

    # These are the extensions supported by the required format
    extensions = post_compilers[compiler]

    # Throw away the post_pages with the wrong extensions
    filtered = [entry for entry in filtered if any([ext in entry[0] for ext in
                                                    extensions])]

    if not filtered:
        type_name = "post" if is_post else "page"
        raise Exception("Can't find a way, using your configuration, to create "
                        "a {0} in format {1}. You may want to tweak "
                        "post_compilers or post_pages in conf.py".format(
                            type_name, compiler))
    return filtered[0]


def get_default_compiler(is_post, post_compilers, post_pages):
    """Given post_compilers and post_pages, return a reasonable
    default compiler for this kind of post/page.
    """

    # First throw away all the post_pages with the wrong is_post
    filtered = [entry for entry in post_pages if entry[3] == is_post]

    # Get extensions in filtered post_pages until one matches a compiler
    for entry in filtered:
        extension = os.path.splitext(entry[0])[-1]
        for compiler, extensions in post_compilers.items():
            if extension in extensions:
                return compiler
    # No idea, back to default behaviour
    return 'rest'


class CommandNewPost(Command):
    """Create a new post."""

    name = "new_post"
    doc_usage = "[options] [path]"
    doc_purpose = "Create a new blog post or site page."
    cmd_options = [
        {
            'name': 'is_page',
            'short': 'p',
            'long': 'page',
            'type': bool,
            'default': False,
            'help': 'Create a page instead of a blog post.'
        },
        {
            'name': 'title',
            'short': 't',
            'long': 'title',
            'type': str,
            'default': '',
            'help': 'Title for the page/post.'
        },
        {
            'name': 'tags',
            'long': 'tags',
            'type': str,
            'default': '',
            'help': 'Comma-separated tags for the page/post.'
        },
        {
            'name': 'onefile',
            'short': '1',
            'type': bool,
            'default': False,
            'help': 'Create post with embedded metadata (single file format)'
        },
        {
            'name': 'twofile',
            'short': '2',
            'type': bool,
            'default': False,
            'help': 'Create post with separate metadata (two file format)'
        },
        {
            'name': 'post_format',
            'short': 'f',
            'long': 'format',
            'type': str,
            'default': '',
            'help': 'Markup format for post, one of rest, markdown, wiki, '
                    'bbcode, html, textile, txt2tags',
        }
    ]

    def _execute(self, options, args):
        """Create a new post or page."""

        compiler_names = [p.name for p in
                          self.site.plugin_manager.getPluginsOfCategory(
                              "PageCompiler")]

        if len(args) > 1:
            print(self.help())
            return False
        elif args:
            path = args[0]
        else:
            path = None

        is_page = options.get('is_page', False)
        is_post = not is_page
        title = options['title'] or None
        tags = options['tags']
        onefile = options['onefile']
        twofile = options['twofile']

        if twofile:
            onefile = False
        if not onefile and not twofile:
            onefile = self.site.config.get('ONE_FILE_POSTS', True)

        post_format = options['post_format']

        if not post_format:  # Issue #400
            post_format = get_default_compiler(
                is_post,
                self.site.config['post_compilers'],
                self.site.config['post_pages'])

        if post_format not in compiler_names:
            print("ERROR: Unknown post format " + post_format)
            return
        compiler_plugin = self.site.plugin_manager.getPluginByName(
            post_format, "PageCompiler").plugin_object

        # Guess where we should put this
        entry = filter_post_pages(post_format, is_post,
                                  self.site.config['post_compilers'],
                                  self.site.config['post_pages'])

        print("Creating New Post")
        print("-----------------\n")
        if title is None:
            print("Enter title: ", end='')
            # WHY, PYTHON3???? WHY?
            sys.stdout.flush()
            title = sys.stdin.readline()
        else:
            print("Title:", title)
        if isinstance(title, utils.bytes_str):
            title = title.decode(sys.stdin.encoding)
        title = title.strip()
        if not path:
            slug = utils.slugify(title)
        else:
            if isinstance(path, utils.bytes_str):
                path = path.decode(sys.stdin.encoding)
            slug = utils.slugify(os.path.splitext(os.path.basename(path))[0])
        date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        data = [title, slug, date, tags]
        output_path = os.path.dirname(entry[0])
        meta_path = os.path.join(output_path, slug + ".meta")
        pattern = os.path.basename(entry[0])
        suffix = pattern[1:]
        if not path:
            txt_path = os.path.join(output_path, slug + suffix)
        else:
            txt_path = path

        if (not onefile and os.path.isfile(meta_path)) or \
                os.path.isfile(txt_path):
            print("The title already exists!")
            exit()

        d_name = os.path.dirname(txt_path)
        if not os.path.exists(d_name):
            os.makedirs(d_name)
        compiler_plugin.create_post(
            txt_path, onefile, title=title,
            slug=slug, date=date, tags=tags)

        if not onefile:  # write metadata file
            with codecs.open(meta_path, "wb+", "utf8") as fd:
                fd.write('\n'.join(data))
            with codecs.open(txt_path, "wb+", "utf8") as fd:
                fd.write("Write your post here.")
            print("Your post's metadata is at: ", meta_path)
        print("Your post's text is at: ", txt_path)
