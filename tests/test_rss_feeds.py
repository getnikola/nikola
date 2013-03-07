# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest
import os
import re
from io import StringIO

import mock

from context import nikola
from lxml import etree


class RSSFeedTest(unittest.TestCase):
    def setUp(self):
        self.blog_url = "http://some.blog"

        with mock.patch('nikola.post.get_meta',
                        mock.Mock(return_value=({'title': 'post title',
                                                 'slug': 'awesome_article',
                                                 'date': '2012-10-01 22:41',
                                                 'tags': 'tags', 'link':
                                                 'link', 'description':
                                                 'description'}))):
            with mock.patch('nikola.nikola.utils.os.path.isdir',
                            mock.Mock(return_value=True)):
                with mock.patch('nikola.nikola.Post.text',
                                mock.Mock(return_value='some long text')):

                    example_post = nikola.nikola.Post('source.file',
                                                      'cache',
                                                      'blog_folder',
                                                      True,
                                                      {'en': ''},
                                                      'en',
                                                      self.blog_url,
                                                      'unused message.',
                                                      'post.tmpl')

                    opener_mock = mock.mock_open()

                    with mock.patch('nikola.nikola.utils.codecs.open', opener_mock, create=True):
                        nikola.nikola.utils.generic_rss_renderer('en',
                                                                 "blog_title",
                                                                 self.blog_url,
                                                                 "blog_description",
                                                                 [example_post,
                                                                  ],
                                                                 'testfeed.rss',
                                                                 True)

                    opener_mock.assert_called_once_with(
                        'testfeed.rss', 'wb+', 'utf-8')

                    # Python 3 / unicode strings workaround
                    # lxml will complain if the encoding is specified in the
                    # xml when running with unicode strings.
                    # We do not include this in our content.
                    open_handle = opener_mock()
                    file_content = [call[1][0]
                                    for call in open_handle.mock_calls[1:-1]][0]
                    splitted_content = file_content.split('\n')
                    self.encoding_declaration = splitted_content[0]
                    content_without_encoding_declaration = splitted_content[1:]
                    self.file_content = '\n'.join(
                        content_without_encoding_declaration)

    def tearDown(self):
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

        et = etree.parse(StringIO(self.file_content))
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
        rss_schema_filename = os.path.join(os.path.dirname(__file__),
                                           'rss-2_0.xsd')
        with open(rss_schema_filename, 'r') as rss_schema_file:
            xmlschema_doc = etree.parse(rss_schema_file)

        xmlschema = etree.XMLSchema(xmlschema_doc)
        document = etree.parse(StringIO(self.file_content))

        self.assertTrue(xmlschema.validate(document))

if __name__ == '__main__':
    unittest.main()
