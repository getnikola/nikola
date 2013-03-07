# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import mock
from nikola.post import get_meta


class dummy(object):
    pass


class GetMetaTest(unittest.TestCase):
    def test_getting_metadata_from_content(self):
        file_metadata = [".. title: Nikola needs more tests!\n",
                         ".. slug: write-tests-now\n",
                         ".. date: 2012/09/15 19:52:05\n",
                         ".. tags:\n",
                         ".. link:\n",
                         ".. description:\n",
                         "Post content\n"]

        opener_mock = mock.mock_open(read_data=file_metadata)
        opener_mock.return_value.readlines.return_value = file_metadata

        post = dummy()
        post.source_path = 'file_with_metadata'
        post.metadata_path = 'file_with_metadata.meta'

        with mock.patch('nikola.post.codecs.open', opener_mock, create=True):
            meta = get_meta(post)

        self.assertEqual('Nikola needs more tests!', meta['title'])
        self.assertEqual('write-tests-now', meta['slug'])
        self.assertEqual('2012/09/15 19:52:05', meta['date'])
        self.assertFalse('tags' in meta)
        self.assertFalse('link' in meta)
        self.assertFalse('description' in meta)

    def test_get_title_from_rest(self):
        file_metadata = [".. slug: write-tests-now\n",
                         ".. date: 2012/09/15 19:52:05\n",
                         ".. tags:\n",
                         ".. link:\n",
                         ".. description:\n",
                         "Post Title\n",
                         "----------\n"]

        opener_mock = mock.mock_open(read_data=file_metadata)
        opener_mock.return_value.readlines.return_value = file_metadata

        post = dummy()
        post.source_path = 'file_with_metadata'
        post.metadata_path = 'file_with_metadata.meta'

        with mock.patch('nikola.post.codecs.open', opener_mock, create=True):
            meta = get_meta(post)

        self.assertEqual('Post Title', meta['title'])
        self.assertEqual('write-tests-now', meta['slug'])
        self.assertEqual('2012/09/15 19:52:05', meta['date'])
        self.assertFalse('tags' in meta)
        self.assertFalse('link' in meta)
        self.assertFalse('description' in meta)

    def test_get_title_from_fname(self):
        file_metadata = [".. slug: write-tests-now\n",
                         ".. date: 2012/09/15 19:52:05\n",
                         ".. tags:\n",
                         ".. link:\n",
                         ".. description:\n"]

        opener_mock = mock.mock_open(read_data=file_metadata)
        opener_mock.return_value.readlines.return_value = file_metadata

        post = dummy()
        post.source_path = 'file_with_metadata'
        post.metadata_path = 'file_with_metadata.meta'

        with mock.patch('nikola.post.codecs.open', opener_mock, create=True):
            meta = get_meta(post, 'file_with_metadata')

        self.assertEqual('file_with_metadata', meta['title'])
        self.assertEqual('write-tests-now', meta['slug'])
        self.assertEqual('2012/09/15 19:52:05', meta['date'])
        self.assertFalse('tags' in meta)
        self.assertFalse('link' in meta)
        self.assertFalse('description' in meta)

    def test_use_filename_as_slug_fallback(self):
        file_metadata = [".. title: Nikola needs more tests!\n",
                         ".. date: 2012/09/15 19:52:05\n",
                         ".. tags:\n",
                         ".. link:\n",
                         ".. description:\n",
                         "Post content\n"]

        opener_mock = mock.mock_open(read_data=file_metadata)
        opener_mock.return_value.readlines.return_value = file_metadata

        post = dummy()
        post.source_path = 'Slugify this'
        post.metadata_path = 'Slugify this.meta'

        with mock.patch('nikola.post.codecs.open', opener_mock, create=True):
            meta = get_meta(post, 'Slugify this')

        self.assertEqual('Nikola needs more tests!', meta['title'])
        self.assertEqual('slugify-this', meta['slug'])
        self.assertEqual('2012/09/15 19:52:05', meta['date'])
        self.assertFalse('tags' in meta)
        self.assertFalse('link' in meta)
        self.assertFalse('description' in meta)

    def test_extracting_metadata_from_filename(self):
        post = dummy()
        post.source_path = '2013-01-23-the_slug-dubdubtitle.md'
        post.metadata_path = '2013-01-23-the_slug-dubdubtitle.meta'
        with mock.patch('nikola.post.codecs.open', create=True):
            meta = get_meta(post,
                            '(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.*)-(?P<title>.*)\.md')

        self.assertEqual('dubdubtitle', meta['title'])
        self.assertEqual('the_slug', meta['slug'])
        self.assertEqual('2013-01-23', meta['date'])

    def test_get_meta_slug_only_from_filename(self):
        post = dummy()
        post.source_path = 'some/path/the_slug.md'
        post.metadata_path = 'some/path/the_slug.meta'
        with mock.patch('nikola.post.codecs.open', create=True):
            meta = get_meta(post)

        self.assertEqual('the_slug', meta['slug'])

if __name__ == '__main__':
    unittest.main()
