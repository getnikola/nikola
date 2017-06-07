# coding: utf8
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


from __future__ import unicode_literals, absolute_import

import os

import io
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO  # NOQA
import tempfile

import docutils
from lxml import html
import unittest

import nikola.plugins.compile.rest
from nikola.plugins.compile.rest import vimeo
import nikola.plugins.compile.rest.listing
from nikola.plugins.compile.rest.doc import Plugin as DocPlugin
from nikola.utils import _reload
from .base import BaseTestCase, FakeSite, FakePost


class ReSTExtensionTestCase(BaseTestCase):
    """ Base class for testing ReST extensions """

    sample = 'foo'
    deps = None

    def setUp(self):
        self.compiler = nikola.plugins.compile.rest.CompileRest()
        self.compiler.set_site(FakeSite())
        return super(ReSTExtensionTestCase, self).setUp()

    def basic_test(self):
        """ Parse cls.sample into a HTML document tree """
        self.setHtmlFromRst(self.sample)

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
        depfile = [p for p in p._depfile[outf] if p != outf]
        depfile = '\n'.join(depfile)
        if depfile:
            self.assertEqual(self.deps.strip(), depfile)
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

    sample = '.. raw:: html\n\n   <iframe src="foo" height="bar">spam</iframe>'

    def test_test(self):
        self.basic_test()
        self.assertHTMLContains("iframe", attributes={"src": "foo"},
                                text="spam")
        self.assertRaises(Exception, self.assertHTMLContains, "eggs", {})


class MathTestCase(ReSTExtensionTestCase):
    sample = ':math:`e^{ix} = \cos x + i\sin x`'

    def test_math(self):
        """ Test that math is outputting TeX code."""
        self.basic_test()
        self.assertHTMLContains("span", attributes={"class": "math"},
                                text="\(e^{ix} = \cos x + i\sin x\)")


class SlidesTestCase(ReSTExtensionTestCase):
    """ Slides test case """

    sample = '.. slides:: IMG.jpg\n'

    def test_slides(self):
        """ Test the slides js generation and img tag creation """
        self.basic_test()
        self.assertHTMLContains("img", attributes={"src": "IMG.jpg"})


class SoundCloudTestCase(ReSTExtensionTestCase):
    """ SoundCloud test case """

    sample = '.. soundcloud:: SID\n   :height: 400\n   :width: 600'

    def test_soundcloud(self):
        """ Test SoundCloud iframe tag generation """
        self.basic_test()
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
        vimeo.Vimeo.request_size = False
        super(VimeoTestCase, self).setUp()
        _reload(nikola.plugins.compile.rest)

    def test_vimeo(self):
        """ Test Vimeo iframe tag generation """
        self.basic_test()
        self.assertHTMLContains("iframe",
                                attributes={"src": ("https://player.vimeo.com/"
                                                    "video/VID"),
                                            "height": "400", "width": "600"})


class YoutubeTestCase(ReSTExtensionTestCase):
    """ Youtube test case """

    sample = '.. youtube:: YID\n   :height: 400\n   :width: 600'

    def test_youtube(self):
        """ Test Youtube iframe tag generation """
        self.basic_test()
        self.assertHTMLContains("iframe",
                                attributes={"src": ("https://www.youtube.com/"
                                                    "embed/YID?rel=0&hd=1&"
                                                    "wmode=transparent"),
                                            "height": "400", "width": "600"})


class ListingTestCase(ReSTExtensionTestCase):
    """ Listing test case and CodeBlock alias tests """

    deps = None
    sample1 = '.. listing:: nikola.py python\n\n'
    sample2 = '.. code-block:: python\n\n   import antigravity'
    sample3 = '.. sourcecode:: python\n\n   import antigravity'

    # def test_listing(self):
    #     """ Test that we can render a file object contents without errors """
    #     with cd(os.path.dirname(__file__)):
    #        self.deps = 'listings/nikola.py'
    #        self.setHtmlFromRst(self.sample1)

    def test_codeblock_alias(self):
        """ Test CodeBlock aliases """
        self.deps = None
        self.setHtmlFromRst(self.sample2)
        self.setHtmlFromRst(self.sample3)


class DocTestCase(ReSTExtensionTestCase):
    """ Ref role test case """

    sample = 'Sample for testing my :doc:`doesnt-exist-post`'
    sample1 = 'Sample for testing my :doc:`fake-post`'
    sample2 = 'Sample for testing my :doc:`titled post <fake-post>`'

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
        self.setHtmlFromRst(self.sample1)
        self.assertHTMLContains('a',
                                text='Fake post',
                                attributes={'href': '/posts/fake-post'})

    def test_doc_titled(self):
        self.setHtmlFromRst(self.sample2)
        self.assertHTMLContains('a',
                                text='titled post',
                                attributes={'href': '/posts/fake-post'})


if __name__ == "__main__":
    unittest.main()
