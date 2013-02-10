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
from optparse import OptionParser
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
        raise Exception("Can't find a way, using your configuration, to create"
                        "a %s in format %s. You may want to tweak "
                        "post_compilers or post_pages in conf.py" %
                        (type_name, compiler))
    return filtered[0]


class CommandNewPost(Command):
    """Create a new post."""

    name = "new_post"

    def run(self, *args):
        """Create a new post."""

        compiler_names = [p.name for p in
                          self.site.plugin_manager.getPluginsOfCategory(
                              "PageCompiler")]

        parser = OptionParser(usage="nikola %s [options]" % self.name)
        parser.add_option('-p', '--page', dest='is_post', action='store_false',
                          default=True, help='Create a page instead of a blog '
                          'post.')
        parser.add_option('-t', '--title', dest='title', help='Title for the '
                          'page/post.', default=None)
        parser.add_option('--tags', dest='tags', help='Comma-separated tags '
                          'for the page/post.', default='')
        parser.add_option('-1', dest='onefile', action='store_true',
                          help='Create post with embedded metadata (single '
                          'file format).',
                          default=self.site.config.get('ONE_FILE_POSTS', True))
        parser.add_option('-2', dest='onefile', action='store_false',
                          help='Create post with separate metadata (two file '
                          'format).',
                          default=self.site.config.get('ONE_FILE_POSTS', True))
        parser.add_option('-f', '--format', dest='post_format', default='rest',
                          help='Format for post (one of %s)' %
                          ','.join(compiler_names))
        (options, args) = parser.parse_args(list(args))

        is_post = options.is_post
        title = options.title
        tags = options.tags
        onefile = options.onefile
        post_format = options.post_format
        if post_format not in compiler_names:
            print("ERROR: Unknown post format %s" % post_format)
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
        if isinstance(title, bytes):
            title = title.decode(sys.stdin.encoding)
        title = title.strip()
        slug = utils.slugify(title)
        date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        data = [title, slug, date, tags]
        output_path = os.path.dirname(entry[0])
        meta_path = os.path.join(output_path, slug + ".meta")
        pattern = os.path.basename(entry[0])
        suffix = pattern[1:]
        txt_path = os.path.join(output_path, slug + suffix)

        if (not onefile and os.path.isfile(meta_path)) or \
                os.path.isfile(txt_path):
            print("The title already exists!")
            exit()
        compiler_plugin.create_post(txt_path, onefile, title, slug, date, tags)

        if not onefile:  # write metadata file
            with codecs.open(meta_path, "wb+", "utf8") as fd:
                fd.write('\n'.join(data))
            with codecs.open(txt_path, "wb+", "utf8") as fd:
                fd.write("Write your post here.")
            print("Your post's metadata is at: ", meta_path)
        print("Your post's text is at: ", txt_path)
