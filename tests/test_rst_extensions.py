# coding: utf8
# Author: Rodrigo Bistolfi
# Date: 03/2013


""" Test cases for Nikola ReST extensions.
A base class ReSTExtensionTestCase provides the tests basic behaivor.
Subclasses must override the "sample" class attribute with the ReST markup.
The sample will be rendered as HTML using publish_parts() by setUp().
One method is provided for checking the resulting HTML:

    * assertHTMLContains(element, attributes=None, text=None)

The HTML is parsed with lxml for checking against the data you provide. The
method takes an element argument, a string representing the *name* of an HTML
tag, like "script" or "iframe". We will try to find this tag in the document
and perform the tests on it. You can pass a dictionary to the attributes kwarg
representing the name and the value of the tag attributes. The text kwarg takes
a string argument, which will be tested against the contents of the HTML
element.
One last caveat: you need to url unquote your urls if you are going to test
attributes like "src" or "link", since the HTML rendered by docutils will be
always unquoted.

"""


from __future__ import unicode_literals

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO  # NOQA

from docutils.core import publish_parts
from lxml import html
import mock

import unittest
import nikola.plugins.compile_rest
from nikola.utils import _reload
from base import BaseTestCase


class ReSTExtensionTestCase(BaseTestCase):
    """ Base class for testing ReST extensions """

    sample = None

    def setUp(self):
        """ Parse cls.sample into a HTML document tree """
        super(ReSTExtensionTestCase, self).setUp()
        self.setHtmlFromRst(self.sample)

    def setHtmlFromRst(self, rst):
        """ Create html output from rst string """
        self.html = publish_parts(rst, writer_name="html")["body"]
        self.html_doc = html.parse(StringIO(self.html))

    def assertHTMLContains(self, element, attributes=None, text=None):
        """ Test if HTML document includes an element with the given
        attributes and text content

        """
        try:
            tag = next(self.html_doc.iter(element))
        except StopIteration:
            raise Exception("<{}> not in {}".format(element, self.html))
        else:
            if attributes:
                arg_attrs = set(attributes.items())
                tag_attrs = set(tag.items())
                self.assertTrue(arg_attrs.issubset(tag_attrs))
            if text:
                self.assertIn(text, tag.text)


class ReSTExtensionTestCaseTestCase(ReSTExtensionTestCase):
    """ Simple test for our base class :) """

    sample = '.. raw:: html\n\n   <iframe src="foo" height="bar">spam</iframe>'

    def test_test(self):
        self.assertHTMLContains("iframe", attributes={"src": "foo"},
                                text="spam")
        self.assertRaises(Exception, self.assertHTMLContains, "eggs", {})


class GistTestCase(ReSTExtensionTestCase):
    """ Test GitHubGist.
    We will replace get_raw_gist() and get_raw_gist_with_filename()
    monkeypatching the GitHubGist class for avoiding network dependency

    """
    gist_type = nikola.plugins.compile_rest.GitHubGist
    sample = '.. gist:: fake_id\n   :file: spam.py'
    sample_without_filename = '.. gist:: fake_id2'

    def setUp(self):
        """ Patch GitHubGist for avoiding network dependency """
        self.gist_type.get_raw_gist_with_filename = lambda *_: 'raw_gist_file'
        self.gist_type.get_raw_gist = lambda *_: "raw_gist"
        _reload(nikola.plugins.compile_rest)

    def test_gist(self):
        """ Test the gist directive with filename """
        self.setHtmlFromRst(self.sample)
        output = 'https://gist.github.com/fake_id.js?file=spam.py'
        self.assertHTMLContains("script", attributes={"src": output})
        self.assertHTMLContains("pre", text="raw_gist_file")

    def test_gist_without_filename(self):
        """ Test the gist directive without filename """
        self.setHtmlFromRst(self.sample_without_filename)
        output = 'https://gist.github.com/fake_id2.js'
        self.assertHTMLContains("script", attributes={"src": output})
        self.assertHTMLContains("pre", text="raw_gist")


class GistIntegrationTestCase(ReSTExtensionTestCase):
    """ Test requests integration. The gist plugin uses requests to fetch gist
    contents and place it in a noscript tag.

    """
    sample = '.. gist:: 1812835'

    def test_gist_integration(self):
        """ Fetch contents of the gist from GH and render in a noscript tag """
        text = ('Be alone, that is the secret of invention: be alone, that is'
                ' when ideas are born. -- Nikola Tesla')
        self.assertHTMLContains('pre', text=text)


class SlidesTestCase(ReSTExtensionTestCase):
    """ Slides test case """

    sample = '.. slides:: IMG.jpg\n'

    def test_slides(self):
        """ Test the slides js generation and img tag creation """
        self.assertHTMLContains("img", attributes={"src": "IMG.jpg"})


class SoundCloudTestCase(ReSTExtensionTestCase):
    """ SoundCloud test case """

    sample = '.. soundcloud:: SID\n   :height: 400\n   :width: 600'

    def test_soundcloud(self):
        """ Test SoundCloud iframe tag generation """
        self.assertHTMLContains("iframe",
                                attributes={"src": ("https://w.soundcloud.com"
                                                    "/player/?url=http://"
                                                    "api.soundcloud.com/"
                                                    "tracks/SID"),
                                            "height": "400", "width": "600"})


class VimeoTestCase(ReSTExtensionTestCase):
    """Vimeo test.
    Set Vimeo.request_size to False for avoiding querying the Vimeo api
    over the network

    """
    sample = '.. vimeo:: VID\n   :height: 400\n   :width: 600'

    def setUp(self):
        """ Disable query of the vimeo api over the wire """
        nikola.plugins.compile_rest.Vimeo.request_size = False
        super(VimeoTestCase, self).setUp()
        _reload(nikola.plugins.compile_rest)

    def test_vimeo(self):
        """ Test Vimeo iframe tag generation """
        self.assertHTMLContains("iframe",
                                attributes={"src": ("http://player.vimeo.com/"
                                                    "video/VID"),
                                            "height": "400", "width": "600"})


class YoutubeTestCase(ReSTExtensionTestCase):
    """ Youtube test case """

    sample = '.. youtube:: YID\n   :height: 400\n   :width: 600'

    def test_youtube(self):
        """ Test Youtube iframe tag generation """
        self.assertHTMLContains("iframe",
                                attributes={"src": ("http://www.youtube.com/"
                                                    "embed/YID?rel=0&hd=1&"
                                                    "wmode=transparent"),
                                            "height": "400", "width": "600"})


class ListingTestCase(ReSTExtensionTestCase):
    """ Listing test case and CodeBlock alias tests """

    sample = '.. listing:: nikola.py python'
    sample2 = '.. code-block:: python\n\n   import antigravity'
    sample3 = '.. sourcecode:: python\n\n   import antigravity'

    opener_mock = mock.mock_open(read_data="import antigravity\n")
    opener_mock.return_value.readlines.return_value = "import antigravity\n"

    def setUp(self):
        """ Inject a mock open function for not generating a test site """
        self.f = StringIO("import antigravity\n")
        #_reload(nikola.plugins.compile_rest)

    def test_listing(self):
        """ Test that we can render a file object contents without errors """
        with mock.patch("nikola.plugins.compile_rest.listing.codecs_open", self.opener_mock, create=True):
            self.setHtmlFromRst(self.sample)

    def test_codeblock_alias(self):
        """ Test CodeBlock aliases """
        with mock.patch("nikola.plugins.compile_rest.listing.codecs_open", self.opener_mock, create=True):
            self.setHtmlFromRst(self.sample2)
            self.setHtmlFromRst(self.sample3)


if __name__ == "__main__":
    unittest.main()
