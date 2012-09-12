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
            help='Format for post (rest or markdown)')
        (options, args) = parser.parse_args(list(args))

        is_post = options.is_post
        title = options.title
        tags = options.tags
        onefile = options.onefile
        post_format = options.post_format

        # Guess where we should put this
        for path, _, _, use_in_rss in self.site.config['post_pages']:
            if use_in_rss == is_post:
                break
        else:
            path = self.site.config['post_pages'][0][0]

        print "Creating New Post"
        print "-----------------\n"
        if title is None:
            title = raw_input("Enter title: ").decode(sys.stdin.encoding)
        else:
            print "Title: ", title
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
            print "The title already exists!"
            exit()

        if onefile:
            if post_format not in ('rest', 'markdown'):
                print "ERROR: Unknown post format %s" % post_format
                return
            with codecs.open(txt_path, "wb+", "utf8") as fd:
                if post_format == 'markdown':
                    fd.write('<!-- \n')
                fd.write('.. title: %s\n' % title)
                fd.write('.. slug: %s\n' % slug)
                fd.write('.. date: %s\n' % date)
                fd.write('.. tags: %s\n' % tags)
                fd.write('.. link: \n')
                fd.write('.. description: \n')
                if post_format == 'markdown':
                    fd.write('-->\n')
                fd.write(u"Write your post here.")
        else:
            with codecs.open(meta_path, "wb+", "utf8") as fd:
                fd.write(data)
            with codecs.open(txt_path, "wb+", "utf8") as fd:
                fd.write(u"Write your post here.")
            print "Your post's metadata is at: ", meta_path
        print "Your post's text is at: ", txt_path


