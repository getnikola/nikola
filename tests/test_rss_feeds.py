# -*- coding: utf-8 -*-

import unittest
import os
import re

import mock

from context import nikola
from lxml.etree import ElementTree


class RSSFeedTest(unittest.TestCase):
    def setUp(self):
        self.feed_filename = 'testfeed.rss'

    def tearDown(self):
        if os.path.exists(self.feed_filename):
            os.remove(self.feed_filename)

    def test_feed_is_valid(self):
        '''
        A testcase to check if the generated feed is valid.

        Validation can be tested with W3 FEED Validator that can be found
        at http://feedvalidator.org
        '''
        # This validation regex is taken from django.core.validators
        url_validation_regex = re.compile(r'^(?:http|ftp)s?://'  # http:// or https://
                                          r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                                          r'localhost|'  # localhost...
                                          r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
                                          r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
                                          r'(?::\d+)?'  # optional port
                                          r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        def is_valid_URL(url):
            return url_validation_regex.match(url) is not None

        def get_metadata(*args, **kwargs):
            return ('post title', 'awesome_article',
                    '2012-10-01 22:41', 'tags', 'link', 'description')

        def get_post_text(*args, **kwargs):
            return 'some long text'

        with mock.patch('nikola.nikola.utils.get_meta', get_metadata):
            with mock.patch('nikola.nikola.utils.os.path.isdir',
                            mock.Mock(return_value=True)):
                with mock.patch('nikola.nikola.Post.text', get_post_text):

                    example_post = nikola.nikola.Post('source.file',
                                                      'blog_folder',
                                                      True,
                                                      {'en': ''},
                                                      'en',
                                                      'http://foo.bar',
                                                      'unused message.')

                    nikola.nikola.utils.generic_rss_renderer('en',
                                                             "blog_title",
                                                             "http://some.blog/",
                                                             "blog_description",
                                                             [example_post, ],
                                                             self.feed_filename)

                    self.assertTrue(os.path.exists(self.feed_filename),
                                    'No feed was created!')

                    et = ElementTree(file=self.feed_filename)
                    channel = et.find('channel')
                    item = channel.find('item')
                    guid = item.find('guid')
                    link = item.find('link')

                    # 1) "link must be a full and valid URL". We will have to
                    # use lxml to make links to posts absolute, it seems.
                    self.assertTrue(is_valid_URL(link.text),
                                    'The following URL is not valid: %s' %
                                    link.text)

                    # 2) "guid must be a full URL, unless isPermaLink attribute
                    # is false: /weblog/posts/the-minimal-server.html "
                    # fixable by setting isPermaLink to false, or by using the
                    # same absolute link as in 1)
                    self.assertTrue(is_valid_URL(guid.text),
                                    'The following URL is not valid: %s' %
                                    guid.text)


if __name__ == '__main__':
    unittest.main()
