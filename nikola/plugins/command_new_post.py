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


class CommandNewPost(Command):
    """Create a new post."""

    name = "new_post"

    def run(self, *args):
        """Create a new post."""
        
        compiler_names = [p.name for p in self.site.plugin_manager.getPluginsOfCategory("PageCompiler")]
        
        parser = OptionParser(usage="nikola %s [options]" % self.name)
        parser.add_option('-p', '--page', dest='is_post',
            action='store_false',
            help='Create a page instead of a blog post.')
        parser.add_option('-t', '--title', dest='title',
            help='Title for the page/post.', default=None)
        parser.add_option('--tags', dest='tags',
            help='Comma-separated tags for the page/post.',
            default='')
        parser.add_option('-1', dest='onefile',
            action='store_true',
            help='Create post with embedded metadata (single file format).',
            default=self.site.config.get('ONE_FILE_POSTS', True))
        parser.add_option('-f', '--format',
            dest='post_format',
            default='rest',
            help='Format for post (one of %s)' % ','.join(compiler_names))
        (options, args) = parser.parse_args(list(args))

        is_post = options.is_post
        title = options.title
        tags = options.tags
        onefile = options.onefile
        post_format = options.post_format
        if post_format not in compiler_names:
            print("ERROR: Unknown post format %s" % post_format)
            return
        compiler_plugin = self.site.plugin_manager.getPluginByName(post_format, "PageCompiler").plugin_object

        # Guess where we should put this
        for path, _, _, use_in_rss in self.site.config['post_pages']:
            if use_in_rss == is_post:
                break
        else:
            path = self.site.config['post_pages'][0][0]

        print("Creating New Post")
        print("-----------------\n")
        if title is None:
            print("Enter title: ")
            title = sys.stdin.readline().decode(sys.stdin.encoding).strip()
        else:
            print("Title: ", title)
        slug = utils.slugify(title)
        date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        data = [
            title,
            slug,
            date,
            tags
            ]
        output_path = os.path.dirname(path)
        meta_path = os.path.join(output_path, slug + ".meta")
        pattern = os.path.basename(path)
        if pattern.startswith("*."):
            suffix = pattern[1:]
        else:
            suffix = ".txt"
        txt_path = os.path.join(output_path, slug + suffix)

        if (not onefile and os.path.isfile(meta_path)) or \
            os.path.isfile(txt_path):
            print("The title already exists!")
            exit()
        compiler_plugin.create_post(txt_path, onefile, title, slug, date, tags)

        if not onefile:  # write metadata file
            with codecs.open(meta_path, "wb+", "utf8") as fd:
                fd.write(data)
            with codecs.open(txt_path, "wb+", "utf8") as fd:
                fd.write("Write your post here.")
            print("Your post's metadata is at: ", meta_path)
        print("Your post's text is at: ", txt_path)
