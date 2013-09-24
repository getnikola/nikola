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
from collections import defaultdict
import math
import re
from textwrap import dedent

from nikola.nikola import Nikola
from nikola.plugin_categories import Command
from nikola.utils import bytes_str, LOGGER, _reload, unicode_str


def add_tags(site, tags, filenames, test_mode=False):
    """ Adds a list of comma-separated tags, given a list of filenames.

        $ nikola tags --add "foo,bar" posts/*.rst

    The above command will add foo and bar tags to all rst posts.

    """

    tags = _process_comma_separated_tags(tags)

    posts = [post for post in site.timeline if post.source_path in filenames]

    if len(tags) == 0 or len(posts) == 0:
        print("ERROR: Need atleast one tag and post.")
        return

    FMT = 'Tags for {0}:\n{1:>6} - {2}\n{3:>6} - {4}\n'
    OLD = 'old'
    NEW = 'new'

    for post in posts:
        new_tags = _add_tags(post.tags[:], tags)

        if test_mode:
            print(FMT.format(
                post.source_path, OLD, post.tags, NEW, new_tags)
            )

        elif new_tags != post.tags:
            _replace_tags_line(post, new_tags)

    return new_tags


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
            show = '{0:>4} {1}'.format(len(site.posts_per_tag[tag]), tag)
        else:
            show = tag
        print(show)

    return tags


def merge_tags(site, tags, filenames, test_mode=False):
    """ Merges a list of comma-separated tags, replacing them with the last tag

    Requires a list of file names to be passed as arguments.

        $ nikola tags --merge "foo,bar,baz,useless" posts/*.rst

    The above command will replace foo, bar, and baz with 'useless'
    in all rst posts.

    """

    tags = _process_comma_separated_tags(tags)

    posts = [post for post in site.timeline if post.source_path in filenames]

    if len(tags) < 2 or len(posts) == 0:
        print("ERROR: Need atleast two tags and a post.")
        return

    FMT = 'Tags for {0}:\n{1:>6} - {2}\n{3:>6} - {4}\n'
    OLD = 'old'
    NEW = 'new'

    for post in posts:
        new_tags = _clean_tags(post.tags[:], set(tags[:-1]), tags[-1])

        if test_mode:
            print(FMT.format(
                post.source_path, OLD, post.tags, NEW, new_tags)
            )

        elif new_tags != post.tags:
            _replace_tags_line(post, new_tags)

    return new_tags


def remove_tags(site, tags, filenames, test_mode=False):
    """ Removes a list of comma-separated tags, given a list of filenames.

        $ nikola tags --remove "foo,bar" posts/*.rst

    The above command will remove foo and bar tags to all rst posts.

    """

    tags = _process_comma_separated_tags(tags)

    posts = [post for post in site.timeline if post.source_path in filenames]

    if len(tags) == 0 or len(posts) == 0:
        print("ERROR: Need atleast one tag and post.")
        return

    FMT = 'Tags for {0}:\n{1:>6} - {2}\n{3:>6} - {4}\n'
    OLD = 'old'
    NEW = 'new'

    if len(posts) == 0:
        new_tags = []

    for post in posts:
        new_tags = _remove_tags(post.tags[:], tags)

        if test_mode:
            print(FMT.format(
                post.source_path, OLD, post.tags, NEW, new_tags)
            )

        elif new_tags != post.tags:
            _replace_tags_line(post, new_tags)

    return new_tags


def search_tags(site, term):
    """ Lists all tags that match the specified search term.

    The tags are sorted alphabetically, by default.

    """

    tags = site.posts_per_tag
    search_re = re.compile(term.lower())

    matches = [
        tag for tag in tags
        if term in tag.lower() or search_re.match(tag.lower())
    ]

    new_tags = sorted(matches, key=lambda tag: tag.lower())

    for tag in new_tags:
        print(tag)

    return new_tags


def sort_tags(site, filenames, test_mode=False):
    """ Sorts all the tags in the given list of posts.

        $ nikola tags --sort posts/*.rst

    The above command will sort all tags alphabetically, in all rst
    posts.  This command can be run on all posts, to clean up things.

    """

    posts = [post for post in site.timeline if post.source_path in filenames]

    if len(posts) == 0:
        LOGGER.error("Need atleast one post.")

        return

    FMT = 'Tags for {0}:\n{1:>6} - {2}\n{3:>6} - {4}\n'
    OLD = 'old'
    NEW = 'new'

    for post in posts:
        new_tags = sorted(post.tags)

        if test_mode:
            print(FMT.format(
                post.source_path, OLD, post.tags, NEW, new_tags)
            )

        elif new_tags != post.tags:
            _replace_tags_line(post, new_tags)

    return new_tags


def _format_doc_string(function):
    text = dedent(' ' * 4 + function.__doc__.strip())
    doc_lines = [line for line in text.splitlines() if line.strip()]
    return '\n'.join(doc_lines) + '\n'


class CommandTags(Command):
    """ Manage tags on the site.

    This plugin is inspired by `jtags <https://github.com/ttscoff/jtag>`_.
    """

    name = "tags"
    doc_usage = "[-t] command [options] [arguments] [filename(s)]"
    doc_purpose = "Command to help manage the tags on your site"
    cmd_options = [
        {
            'name': 'add',
            'long': 'add',
            'short': 'a',
            'default': '',
            'type': str,
            'help': _format_doc_string(add_tags)
        },
        {
            'name': 'list',
            'long': 'list',
            'short': 'l',
            'default': False,
            'type': bool,
            'help': _format_doc_string(list_tags)
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
            'help': _format_doc_string(merge_tags)
        },
        {
            'name': 'remove',
            'long': 'remove',
            'short': 'r',
            'default': '',
            'type': str,
            'help': _format_doc_string(remove_tags)
        },
        {
            'name': 'search',
            'long': 'search',
            'default': '',
            'type': str,
            'help': _format_doc_string(search_tags)
        },
        {
            'name': 'sort',
            'long': 'sort',
            'short': 'S',
            'default': False,
            'type': bool,
            'help': _format_doc_string(sort_tags)
        },
        {
            'name': 'tag',
            'long': 'tag',
            'default': False,
            'type': bool,
            'help': 'Automatically tag a given set of posts.'
        },
        {
            'name': 'test',
            'short': 't',
            'type': bool,
            'default': False,
            'help': 'Run other commands in test mode (no files are edited).\n'
        },

    ]

    def _execute(self, options, args):
        """Manage the tags on the site."""

        try:
            import conf

        except ImportError:
            LOGGER.error("No configuration found, cannot run the console.")

        else:
            _reload(conf)
            nikola = Nikola(**conf.__dict__)
            nikola.scan_posts()

            if len(options['add']) > 0 and len(args) > 0:
                add_tags(nikola, options['add'], args, options['test'])

            elif options['list']:
                list_tags(nikola, options['list_sorting'])

            elif options['merge'].count(',') > 0 and len(args) > 0:
                merge_tags(nikola, options['merge'], args, options['test'])

            elif len(options['remove']) > 0 and len(args) > 0:
                remove_tags(nikola, options['remove'], args, options['test'])

            elif len(options['search']) > 0:
                search_tags(nikola, options['search'])

            elif options['tag'] and len(args) > 0:
                tagger = _AutoTag(nikola)
                for post in args:
                    tags = ','.join(tagger.tag(post))
                    add_tags(nikola, tags, [post], options['test'])

            elif options['sort'] and len(args) > 0:
                sort_tags(nikola, args, options['test'])

            else:
                print(self.help())


#### Private definitions ######################################################

class _AutoTag(object):
    """ A class to auto tag posts, using tf-idf. """

    WORDS = '([A-Za-z]+[A-Za-z-]*[A-Za-z]+|[A-Za-z]+)'

    def tag(self, post, count=5):
        """ Return a list of top tags, given a post.

        post: can either be a post object or the source path
        count: the number of tags to return

        """

        if isinstance(post, (bytes_str, unicode_str)):
            source_path = post
            post = self._get_post_from_source_path(source_path)
            if post is None:
                LOGGER.error('No post found for path: %s' % source_path)
                return

        return self._find_top_scoring_tags(post, count)

    #### 'object' interface ###################################################

    def __init__(self, site, use_nltk=True):
        """ Set up a dictionary of documents.

        Each post is mapped to a list of words it contains.

        """

        self._site = site
        self._documents = {}
        self._stem_cache = {}
        self._use_nltk = use_nltk and self._nltk_available()

        if self._use_nltk:
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            from nltk.stem import SnowballStemmer

            self._tag_pattern = re.compile(self.WORDS + '$')
            self._tokenize = word_tokenize
            self._stem_word_mapping = defaultdict(set)
            self._stemmer = SnowballStemmer('porter')
            self._stopwords = set(stopwords.words())

        else:
            self._tag_pattern = re.compile(self.WORDS)

        self._process_posts()
        self._document_count = len(self._documents)

    #### 'Private' interface ##################################################

    def _find_stems_for_words_in_documents(self, text):
        """ Process text to get list of stems. """

        words = []

        for word in self._tokenize(text):
            if self._tag_pattern.match(word) is not None:
                if word not in self._stopwords:
                    words.append(self._get_stem_from_cache(word))

        return words

    def _find_top_scoring_tags(self, post, count):
        """ Return the tags with the top tf-idf score. """

        tf_idf_table = {}

        for word in self._documents[post.source_path]:
            tf_idf_table[word] = self._tf_idf(word, post)
            tags = sorted(
                tf_idf_table, key=lambda x: tf_idf_table[x], reverse=True
            )

        if self._use_nltk:
            tags = [
                sorted(self._stem_word_mapping[tag], key=len)[0]
                for tag in tags[:count]
            ]

        else:
            tags = tags[:count]

        return tags

    def _get_post_from_source_path(self, source):
        """ Return a post given the source path. """

        posts = [
            post for post in self._site.timeline
            if post.source_path == source
        ]

        post = posts[0] if len(posts) == 1 else None

        return post

    def _get_post_text(self, post):
        """ Return the text of a given post. """

        with codecs.open(post.source_path, 'r', 'utf-8') as post_file:
            post_text = post_file.read().lower()
            if not post.is_two_file:
                post_text = post_text.split('\n\n', 1)[-1]

        return post_text

    def _get_word_count(self, post):
        """ Get the count of all words in a given post. """

        word_counts = defaultdict(lambda: 0)

        for word in self._documents[post.source_path]:
            word_counts[word] += 1

        return word_counts

    def _get_stem_from_cache(self, word):
        """ Return the stem for a word, and cache it, if required. """

        if word not in self._stem_cache:
            stem = self._stemmer.stem(word)
            self._stem_cache[word] = stem
            self._stem_word_mapping[stem].add(word)
        else:
            stem = self._stem_cache[word]

        return stem

    def _inverse_document_frequency(self, word):
        """ Gets the inverse document frequency of a word. """

        count = sum(1 for doc in self._documents.values()
                    if word.lower() in doc)

        return math.log(self._document_count / float(count))

    def _nltk_available(self):
        """ Return True if we can import nltk. """

        try:
            import nltk
        except ImportError:
            nltk = None

        return nltk is not None

    def _process_posts(self):
        """ Tokenize the posts (and stem the words, if use_nltk). """

        for post in self._site.timeline:

            text = self._get_post_text(post)

            if not self._use_nltk:
                words = self._tag_pattern.findall(text)

            else:
                words = self._find_stems_for_words_in_documents(text)

            self._documents[post.source_path] = words

    def _term_frequncy(self, word, post):
        """ Returns the frequency of a word, given a post.

        # fixme: using stopwords may be necessary, if number of
        # documents is small.  (not for small initial number of posts)

        """

        word_counts = self._get_word_count(post)

        # A mix of augmented, logarithmic frequency.  We divide with
        # the max frequency to prevent a bias towards longer document.
        tf = math.log(
            1 + float(word_counts[word]) / max(word_counts.values())
        )

        return tf

    def _tf_idf(self, word, post):
        """ Return tf-idf value of a word, in a specified post. """

        tf = self._term_frequncy(word, post)
        idf = self._inverse_document_frequency(word)

        return tf * idf


def _add_tags(tags, additions):
    """ In all tags list, add tags in additions if not already present. """

    for tag in additions:
        if tag not in tags:
            tags.append(tag)

    return tags


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
    """ Return a list of tags given a string of comma-separated tags. """
    return [tag.strip() for tag in tags.strip().split(',') if tag.strip()]


def _remove_tags(tags, removals):
    """ In all tags list, remove tags in removals. """

    for tag in removals:
        while tag in tags:
            tags.remove(tag)

    return tags


def _replace_tags_line(post, tags):
    """ Replaces the line that lists the tags, with given tags. """

    source_path = post.source_path

    if post.is_two_file:
        # fixme: currently doesn't handle two post files.
        LOGGER.error(
            "Two file posts are not supported, currently."
            "Skipping %s" % source_path
        )

        return

    with codecs.open(source_path, 'r', 'utf-8') as f:
        post_text = f.readlines()

    tag_identifier = u'.. tags:'
    new_tags = u'.. tags: %s\n' % ', '.join(tags)

    for index, line in enumerate(post_text[:]):
        if line.startswith(tag_identifier):
            post_text[index] = new_tags
            break

    with codecs.open(source_path, 'w+', 'utf-8') as f:
        post_text = f.writelines(post_text)
