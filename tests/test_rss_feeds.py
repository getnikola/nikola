# -*- coding: utf-8 -*-

import unittest
import os
import re

import mock

from context import nikola
from lxml.etree import ElementTree
from lxml import etree


class RSSFeedTest(unittest.TestCase):
    def setUp(self):
        self.feed_filename = 'testfeed.rss'
        self.blog_url = "http://some.blog"

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
                                                      self.blog_url,
                                                      'unused message.')

                    nikola.nikola.utils.generic_rss_renderer('en',
                                                             "blog_title",
                                                             self.blog_url,
                                                             "blog_description",
                                                             [example_post, ],
                                                             self.feed_filename)

                    self.assertTrue(os.path.exists(self.feed_filename),
                                    'No feed was created!')

    def tearDown(self):
        if os.path.exists(self.feed_filename):
            #os.remove(self.feed_filename)
            pass

    def test_feed_items_have_valid_URLs(self):
        '''The items in the feed need to have valid urls in link and guid.'''
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

        et = ElementTree(file=self.feed_filename)
        channel = et.find('channel')
        item = channel.find('item')
        guid = item.find('guid')
        link = item.find('link')

        # As stated by W3 FEED Validator: "link must be a full and valid URL"
        self.assertTrue(is_valid_URL(link.text),
                        'The following URL is not valid: %s' % link.text)
        self.assertTrue(self.blog_url in link.text)

        # "guid must be a full URL, unless isPermaLink attribute
        # is false: /weblog/posts/the-minimal-server.html "
        self.assertTrue(is_valid_URL(guid.text),
                        'The following URL is not valid: %s' %
                        guid.text)
        self.assertTrue(self.blog_url in guid.text)

    def test_feed_is_valid(self):
        '''
        A testcase to check if the generated feed is valid.

        Validation can be tested with W3 FEED Validator that can be found
        at http://feedvalidator.org
        '''
        with open('rss-2_0.xsd', 'r') as rss20_schema_file:
            schema_root = etree.XML(''.join(rss20_schema_file.readlines()))
            schema = etree.XMLSchema(schema_root)
            parser = etree.XMLParser(schema=schema)

            with open(self.feed_filename, 'r') as feed_file:
                # parsing the created file with the parser will
                # throw errors if the scheme is not followed
                root = etree.fromstringlist(feed_file.readlines(), parser)


if __name__ == '__main__':
    unittest.main()
