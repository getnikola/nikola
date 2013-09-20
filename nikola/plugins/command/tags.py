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

from __future__ import unicode_literals, print_function
import codecs
from textwrap import dedent

from nikola.nikola import Nikola
from nikola.plugin_categories import Command
from nikola.utils import LOGGER


def format_doc_string(function):
    text = dedent(' ' * 4 + function.__doc__.strip())
    return '\n'.join([line for line in text.splitlines() if line.strip()]) + '\n'


def list_tags(site, sorting='alpha'):
    """ Lists all the tags used in the site.

    The tags are sorted alphabetically, by default.  Sorting can be
    one of 'alpha' or 'count'.

    """

    tags = site.posts_per_tag
    if sorting == 'count':
        tags = sorted(tags, key=lambda tag: len(tags[tag]), reverse=True)
    else:
        tags = sorted(site.posts_per_tag.keys())

    for tag in tags:
        if sorting == 'count':
            show = '{:>4} {}'.format(len(site.posts_per_tag[tag]), tag)
        else:
            show = tag
        print(show)

    return tags


def merge_tags(site, tags, filenames, test_mode=False):
    """ Merges a list of comma-separated tags, replacing them with the last tag.

    Requires a list of file names to be passed as arguments.

        $ nikola tags --merge "foo,bar,baz,useless" posts/*.rst

    The above command will replace foo, bar, and baz with 'useless'
    in all rst posts.

    """

    tags = _process_comma_separated_tags(tags)

    if len(tags) < 2:
        print("ERROR: Need atleast two tags to merge.")

    else:
        # fixme: currently doesn't handle two post files.
        posts = [
            post for post in site.timeline
            if post.source_path in filenames and not post.is_two_file
        ]
        FMT = 'Tags for {0}:\n{1:>6} - {2}\n{3:>6} - {4}\n'
        OLD = 'old'
        NEW = 'new'
        for post in posts:
            new_tags = _clean_tags(post.alltags[:], set(tags[:-1]), tags[-1])
            if test_mode:
                print(FMT.format(
                    post.source_path, OLD, post.alltags, NEW, new_tags)
                )
            else:
                _replace_tags_line(post, new_tags)

    return new_tags


def _clean_tags(tags, remove, keep):
    """ In all tags list, replace tags in remove with keep tag. """
    original_tags = tags[:]
    for index, tag in enumerate(original_tags):
        if tag in remove:
            tags.remove(tag)

    if len(original_tags) != len(tags) and keep not in tags:
        tags.append(keep)

    return tags

def _process_comma_separated_tags(tags):
    return [tag.strip() for tag in tags.strip().split(',')]

def _replace_tags_line(post, tags):
    with codecs.open(post.source_path) as f:
        post_text = f.readlines()

    for index, line in enumerate(post_text[:]):
        if line.startswith('.. tags:'):
            post_text[index] = '.. tags: %s\n' % ', '.join(tags)
            break

    with codecs.open(post.source_path, 'wb+') as f:
        post_text = f.writelines(post_text)


class CommandTags(Command):
    """ Manage tags on the site.

    This plugin is inspired by `jtags <https://github.com/ttscoff/jtag>`_.
    """

    name = "tags"
    doc_usage = "[options]"
    doc_purpose = "manages the tags of your site"
    cmd_options = [
        {
            'name': 'list',
            'long': 'list',
            'short': 'l',
            'default': False,
            'type': bool,
            'help': format_doc_string(list_tags)
        },
        {
            'name': 'list_sorting',
            'short': 's',
            'type': str,
            'default': 'alpha',
            'help': 'Changes sorting of list; can be one of alpha or count.\n'
        },
        {
            'name': 'merge',
            'long': 'merge',
            'type': str,
            'default': '',
            'help': format_doc_string(merge_tags)
        },
        {
            'name': 'test',
            'short': 't',
            'type': bool,
            'default': False,
            'help': 'Run other commands in test mode.  Does not edit any files.\n'
        },

    ]

    def _execute(self, options, args):
        """Manage the tags on the site."""

        try:
            import conf

        except ImportError:
            LOGGER.error("No configuration found, cannot run the console.")

        else:
            nikola = Nikola(**conf.__dict__)
            nikola.scan_posts()

            if len(options['merge']) > 1 and len(args) > 0:
                merge_tags(nikola, options['merge'], args, options['test'])

            elif options['list']:
                list_tags(nikola, options['list_sorting'])

            else:
                print(self.help())
