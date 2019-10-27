# Author: Rodrigo Bistolfi
# Date: 03/2013


""" Test cases for Nikola ReST extensions.
A base class ReSTExtensionTestCase provides the tests basic behaviour.
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

import io
import os
import tempfile
import unittest
from io import StringIO

import docutils
from lxml import html

import nikola.plugins.compile.rest
import nikola.plugins.compile.rest.listing
from nikola.plugins.compile.rest import vimeo
from nikola.plugins.compile.rest.doc import Plugin as DocPlugin
from nikola.utils import _reload, LocaleBorg

from .base import BaseTestCase, FakeSite, FakePost

import pytest


@pytest.fixture(autouse=True, scope="module")
def localeborg_base():
    """A base config of LocaleBorg."""
    LocaleBorg.reset()
    assert not LocaleBorg.initialized
    LocaleBorg.initialize({}, 'en')
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == 'en'
    try:
        yield
    finally:
        LocaleBorg.reset()
        assert not LocaleBorg.initialized


class ReSTExtensionTestCase(BaseTestCase):
    """ Base class for testing ReST extensions """

    sample = 'foo'

    def setUp(self):
        self.compiler = nikola.plugins.compile.rest.CompileRest()
        self.compiler.set_site(FakeSite())
        return super(ReSTExtensionTestCase, self).setUp()

    def setHtmlFromRst(self, rst):
        """ Create html output from rst string """
        tmpdir = tempfile.mkdtemp()
        inf = os.path.join(tmpdir, 'inf')
        outf = os.path.join(tmpdir, 'outf')
        with io.open(inf, 'w+', encoding='utf8') as f:
            f.write(rst)
        p = FakePost('', '')
        p._depfile[outf] = []
        self.compiler.site.post_per_input_file[inf] = p
        self.html = self.compiler.compile(inf, outf)
        with io.open(outf, 'r', encoding='utf8') as f:
            self.html = f.read()
        os.unlink(inf)
        os.unlink(outf)
        os.rmdir(tmpdir)
        self.html_doc = html.parse(StringIO(self.html))

    def assertHTMLContains(self, element, attributes=None, text=None):
        """ Test if HTML document includes an element with the given
        attributes and text content

        """
        try:
            tag = next(self.html_doc.iter(element))
        except StopIteration:
            raise Exception("<{0}> not in {1}".format(element, self.html))
        else:
            if attributes:
                arg_attrs = set(attributes.items())
                tag_attrs = set(tag.items())
                self.assertTrue(arg_attrs.issubset(tag_attrs))
            if text:
                self.assertIn(text, tag.text)


class ReSTExtensionTestCaseTestCase(ReSTExtensionTestCase):
    """ Simple test for our base class :) """

    def test_test(self):
        sample = '.. raw:: html\n\n   <iframe src="foo" height="bar">spam</iframe>'
        self.setHtmlFromRst(sample)
        self.assertHTMLContains("iframe", attributes={"src": "foo"},
                                text="spam")
        self.assertRaises(Exception, self.assertHTMLContains, "eggs", {})


class MathTestCase(ReSTExtensionTestCase):

    def test_math(self):
        """ Test that math is outputting TeX code."""
        sample = r':math:`e^{ix} = \cos x + i\sin x`'
        self.setHtmlFromRst(sample)
        self.assertHTMLContains("span", attributes={"class": "math"},
                                text=r"\(e^{ix} = \cos x + i\sin x\)")


class SoundCloudTestCase(ReSTExtensionTestCase):
    """ SoundCloud test case """

    def test_soundcloud(self):
        """ Test SoundCloud iframe tag generation """
        sample = '.. soundcloud:: SID\n   :height: 400\n   :width: 600'
        self.setHtmlFromRst(sample)
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

    def setUp(self):
        """ Disable query of the vimeo api over the wire """
        vimeo.Vimeo.request_size = False
        super(VimeoTestCase, self).setUp()
        _reload(nikola.plugins.compile.rest)

    def test_vimeo(self):
        """ Test Vimeo iframe tag generation """
        sample = '.. vimeo:: VID\n   :height: 400\n   :width: 600'
        self.setHtmlFromRst(sample)
        self.assertHTMLContains("iframe",
                                attributes={"src": ("https://player.vimeo.com/"
                                                    "video/VID"),
                                            "height": "400", "width": "600"})


class YoutubeTestCase(ReSTExtensionTestCase):
    """ Youtube test case """

    def test_youtube(self):
        """ Test Youtube iframe tag generation """
        sample = '.. youtube:: YID\n   :height: 400\n   :width: 600'
        self.setHtmlFromRst(sample)
        self.assertHTMLContains("iframe",
                                attributes={"src": ("https://www.youtube-nocookie.com/"
                                                    "embed/YID?rel=0&"
                                                    "wmode=transparent"),
                                            "height": "400", "width": "600",
                                            "frameborder": "0", "allowfullscreen": "",
                                            "allow": "encrypted-media"})


class ListingTestCase(ReSTExtensionTestCase):
    """ Listing test case and CodeBlock alias tests """

    def test_codeblock_alias(self):
        """ Test CodeBlock aliases """
        sample2 = '.. code-block:: python\n\n   import antigravity'
        self.setHtmlFromRst(sample2)

        sample3 = '.. sourcecode:: python\n\n   import antigravity'
        self.setHtmlFromRst(sample3)


class DocTestCase(ReSTExtensionTestCase):
    """ Ref role test case """

    def setUp(self):
        # Initialize plugin, register role
        self.plugin = DocPlugin()
        self.plugin.set_site(FakeSite())
        # Hack to fix leaked state from integration tests
        try:
            f = docutils.parsers.rst.roles.role('doc', None, None, None)[0]
            f.site = FakeSite()
        except AttributeError:
            pass
        return super(DocTestCase, self).setUp()

    def test_doc_doesnt_exist(self):
        self.assertRaises(Exception, self.assertHTMLContains, 'anything', {})

    def test_doc(self):
        sample1 = 'Sample for testing my :doc:`fake-post`'
        self.setHtmlFromRst(sample1)
        self.assertHTMLContains('a',
                                text='Fake post',
                                attributes={'href': '/posts/fake-post'})

    def test_doc_titled(self):
        sample2 = 'Sample for testing my :doc:`titled post <fake-post>`'
        self.setHtmlFromRst(sample2)
        self.assertHTMLContains('a',
                                text='titled post',
                                attributes={'href': '/posts/fake-post'})


if __name__ == "__main__":
    unittest.main()
