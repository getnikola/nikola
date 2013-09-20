# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from context import nikola

import os
import shutil
import tempfile
import unittest
import sys

from nikola.plugins.command.tags import (
    add_tags, list_tags, merge_tags, remove_tags, search_tags, sort_tags
)


DEMO_TAGS = ['python', 'demo', 'nikola', 'blog']


class TestCommandTags(unittest.TestCase):

    #### `TestCase` protocol ##################################################

    def setUp(self):
        """ Create a demo site, for testing. """

        self._create_temp_dir_and_cd()
        self._init_site()

    def tearDown(self):
        """ Restore world order. """
        self._remove_temp_dir()

    #### `TestCommandTags` protocol ###########################################

    def test_add(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]
        tags = 'test_nikola'

        new_tags = add_tags(self._site, tags, posts)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertIn('test_nikola', new_tags)
        self.assertEquals(set(new_tags), set(new_parsed_tags))

    def test_add_test_mode(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]
        tags = 'test_nikola'

        new_tags = add_tags(self._site, tags, posts, test_mode=True)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertIn('test_nikola', new_tags)
        self.assertEquals(set(new_parsed_tags), set(DEMO_TAGS))

    def test_list(self):
        self.assertEquals(sorted(DEMO_TAGS), list_tags(self._site))

    def test_list_count_sorted(self):
        self._add_test_post(title='2', tags=['python'])
        tags = list_tags(self._site, 'count')
        self.assertEquals('python', tags[0])

    def test_merge(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]
        tags = 'nikola, python'

        new_tags = merge_tags(self._site, tags, posts)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertNotIn('nikola', new_tags)
        self.assertEquals(set(new_tags), set(new_parsed_tags))

    def test_merge_test_mode(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]
        tags = 'nikola, python'

        new_tags = merge_tags(self._site, tags, posts, test_mode=True)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertNotIn('nikola', new_tags)
        self.assertEquals(set(DEMO_TAGS), set(new_parsed_tags))

    def test_remove(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]
        tags = 'nikola'

        new_tags = remove_tags(self._site, tags, posts)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertNotIn('nikola', new_tags)
        self.assertEquals(set(new_tags), set(new_parsed_tags))

    def test_remove_invalid(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]
        tags = 'wordpress'

        new_tags = remove_tags(self._site, tags, posts)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertEquals(set(new_tags), set(new_parsed_tags))

    def test_remove_test_mode(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]
        tags = 'nikola'

        new_tags = remove_tags(self._site, tags, posts, test_mode=True)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertNotIn('nikola', new_tags)
        self.assertEquals(set(new_parsed_tags), set(DEMO_TAGS))

    def test_search(self):
        search_terms = {
            'l': ['blog', 'nikola'],
            '.*': sorted(DEMO_TAGS),
            '^ni.*': ['nikola']
        }
        for term in search_terms:
            tags = search_tags(self._site, term)
            self.assertEquals(tags, search_terms[term])

    def test_sort(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]

        new_tags = sort_tags(self._site, posts)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertEquals(sorted(DEMO_TAGS), new_parsed_tags)
        self.assertEquals(sorted(DEMO_TAGS), new_tags)

    def test_sort_test_mode(self):
        posts = [os.path.join('posts', post) for post in os.listdir('posts')]

        new_tags = sort_tags(self._site, posts, test_mode=True)
        new_parsed_tags = self._parse_new_tags(posts[0])

        self.assertEquals(DEMO_TAGS, new_parsed_tags)
        self.assertEquals(sorted(DEMO_TAGS), new_tags)

    #### Private protocol #####################################################

    def _add_test_post(self, title, tags):
        self._run_command(['new_post', '-t', title, '--tags', ','.join(tags)])

    def _create_temp_dir_and_cd(self):
        self._testdir = tempfile.mkdtemp()
        self._old_dir = os.getcwd()
        os.chdir(self._testdir)

    def _init_site(self):
        from nikola.plugins.command.init import CommandInit

        command_init = CommandInit()
        command_init.execute(options={'demo': True}, args=['demo'])

        sys.path.insert(0, '')
        os.chdir('demo')

        import conf
        self._site = nikola.Nikola(**conf.__dict__)
        self._site.scan_posts()

    def _parse_new_tags(self, source):
        """ Returns the new tags for a post, given it's source path. """
        self._site._scanned = False
        self._site.scan_posts()
        posts = [
            post for post in self._site.timeline
            if post.source_path == source
        ]
        return posts[0].alltags

    def _remove_temp_dir(self):
        os.chdir(self._old_dir)
        shutil.rmtree(self._testdir)

    def _run_command(self, args=[]):
        from nikola.main import main
        return main(args)


if __name__ == '__main__':
    unittest.main()
