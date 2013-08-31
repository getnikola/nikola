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

import codecs
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO  # NOQA
import os
import sys
import tempfile

from lxml import html
from nose.plugins.skip import SkipTest
import unittest
from yapsy.PluginManager import PluginManager

from nikola import utils
import nikola.plugins.compile.rest
from nikola.plugins.compile.rest import gist
from nikola.plugins.compile.rest import vimeo
import nikola.plugins.compile.rest.listing
from nikola.utils import _reload
from nikola.plugin_categories import (
    Command,
    Task,
    LateTask,
    TemplateSystem,
    PageCompiler,
    TaskMultiplier,
    RestExtension,
)
from base import BaseTestCase


class FakeSite(object):
    def __init__(self):
        self.template_system = self
        self.config = {
            'DISABLED_PLUGINS': [],
            'EXTRA_PLUGINS': [],
        }
        self.EXTRA_PLUGINS = self.config['EXTRA_PLUGINS']
        self.plugin_manager = PluginManager(categories_filter={
            "Command": Command,
            "Task": Task,
            "LateTask": LateTask,
            "TemplateSystem": TemplateSystem,
            "PageCompiler": PageCompiler,
            "TaskMultiplier": TaskMultiplier,
            "RestExtension": RestExtension,
        })
        self.plugin_manager.setPluginInfoExtension('plugin')
        if sys.version_info[0] == 3:
            places = [
                os.path.join(os.path.dirname(utils.__file__), 'plugins'),
            ]
        else:
            places = [
                os.path.join(os.path.dirname(utils.__file__), utils.sys_encode('plugins')),
            ]
        self.plugin_manager.setPluginPlaces(places)
        self.plugin_manager.collectPlugins()

    def render_template(self, name, _, context):
        return('<img src="IMG.jpg">')


class ReSTExtensionTestCase(BaseTestCase):
    """ Base class for testing ReST extensions """

    sample = 'foo'

    def setUp(self):
        """ Parse cls.sample into a HTML document tree """
        super(ReSTExtensionTestCase, self).setUp()
        self.compiler = nikola.plugins.compile.rest.CompileRest()
        self.compiler.set_site(FakeSite())
        self.setHtmlFromRst(self.sample)

    def setHtmlFromRst(self, rst):
        """ Create html output from rst string """
        tmpdir = tempfile.mkdtemp()
        inf = os.path.join(tmpdir, 'inf')
        outf = os.path.join(tmpdir, 'outf')
        with codecs.open(inf, 'wb+', 'utf8') as f:
            f.write(rst)
        self.html = self.compiler.compile_html(inf, outf)
        with codecs.open(outf, 'r', 'utf8') as f:
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


class MathTestCase(ReSTExtensionTestCase):
    sample = ':math:`e^{ix} = \cos x + i\sin x`'

    def test_mathjax(self):
        """ Test that math is outputting MathJax."""
        self.assertHTMLContains("span", attributes={"class": "math"},
                                text="\(e^{ix} = \cos x + i\sin x\)")


class GistTestCase(ReSTExtensionTestCase):
    """ Test GitHubGist.
    We will replace get_raw_gist() and get_raw_gist_with_filename()
    monkeypatching the GitHubGist class for avoiding network dependency

    """
    gist_type = gist.GitHubGist
    sample = '.. gist:: fake_id\n   :file: spam.py'
    sample_without_filename = '.. gist:: fake_id2'

    def setUp(self):
        """ Patch GitHubGist for avoiding network dependency """
        self.gist_type.get_raw_gist_with_filename = lambda *_: 'raw_gist_file'
        self.gist_type.get_raw_gist = lambda *_: "raw_gist"
        _reload(nikola.plugins.compile.rest)

    def test_gist(self):
        """ Test the gist directive with filename """
        raise SkipTest
        self.setHtmlFromRst(self.sample)
        output = 'https://gist.github.com/fake_id.js?file=spam.py'
        self.assertHTMLContains("script", attributes={"src": output})
        self.assertHTMLContains("pre", text="raw_gist_file")

    def test_gist_without_filename(self):
        """ Test the gist directive without filename """
        raise SkipTest
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
        vimeo.Vimeo.request_size = False
        super(VimeoTestCase, self).setUp()
        _reload(nikola.plugins.compile.rest)

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

    sample1 = '.. listing:: nikola.py python'
    sample2 = '.. code-block:: python\n\n   import antigravity'
    sample3 = '.. sourcecode:: python\n\n   import antigravity'

    def setUp(self):
        """ Inject a mock open function for not generating a test site """
        self.f = StringIO("import antigravity\n")
        super(ListingTestCase, self).setUp()
        pi = self.compiler.site.plugin_manager.getPluginByName('listing', 'RestExtension')
        # THERE MUST BE A NICER WAY

        def fake_open(*a, **kw):
            return self.f

        sys.modules[pi.plugin_object.__module__].codecs_open = fake_open

    def test_listing(self):
        """ Test that we can render a file object contents without errors """
        self.setHtmlFromRst(self.sample1)

    def test_codeblock_alias(self):
        """ Test CodeBlock aliases """
        self.setHtmlFromRst(self.sample2)
        self.setHtmlFromRst(self.sample3)


if __name__ == "__main__":
    unittest.main()
