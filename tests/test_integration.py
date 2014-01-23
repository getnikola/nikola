# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

# This code is so you can run the samples without installing the package,
# and should be before any import touching nikola, in any file under tests/
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


import codecs
import locale
import shutil
import tempfile
import unittest

import lxml.html
from nose.plugins.skip import SkipTest

from nikola import __main__
import nikola
import nikola.plugins.command
import nikola.plugins.command.init

from .base import BaseTestCase, cd


class EmptyBuildTest(BaseTestCase):
    """Basic integration testcase."""

    dataname = None

    @classmethod
    def setUpClass(cls):
        """Setup a demo site."""
        cls.tmpdir = tempfile.mkdtemp()
        cls.target_dir = os.path.join(cls.tmpdir, "target")
        cls.init_command = nikola.plugins.command.init.CommandInit()
        cls.fill_site()
        cls.patch_site()
        cls.build()

    @classmethod
    def fill_site(self):
        """Add any needed initial content."""
        self.init_command.create_empty_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)

        if self.dataname:
            src = os.path.join(os.path.dirname(__file__), 'data',
                               self.dataname)
            for root, dirs, files in os.walk(src):
                for src_name in files:
                    rel_dir = os.path.relpath(root, src)
                    dst_file = os.path.join(self.target_dir, rel_dir, src_name)
                    src_file = os.path.join(root, src_name)
                    shutil.copy2(src_file, dst_file)

    @classmethod
    def patch_site(self):
        """Make any modifications you need to the site."""

    @classmethod
    def build(self):
        """Build the site."""
        with cd(self.target_dir):
            __main__.main(["build"])

    @classmethod
    def tearDownClass(self):
        """Remove the demo site."""
        # ignore_errors=True for windows by issue #782
        shutil.rmtree(self.tmpdir, ignore_errors=(sys.platform == 'win32'))
        # Fixes Issue #438
        try:
            del sys.modules['conf']
        except KeyError:
            pass

    def test_build(self):
        """Ensure the build did something."""
        index_path = os.path.join(
            self.target_dir, "output", "archive.html")
        self.assertTrue(os.path.isfile(index_path))


class DemoBuildTest(EmptyBuildTest):
    """Test that a default build of --demo works."""

    @classmethod
    def fill_site(self):
        """Fill the site with demo content."""
        self.init_command.copy_sample_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)
        # File for Issue #374 (empty post text)
        with codecs.open(os.path.join(self.target_dir, 'posts', 'empty.txt'), "wb+", "utf8") as outf:
            outf.write(
                ".. title: foobar\n"
                ".. slug: foobar\n"
                ".. date: 2013-03-06 19:08:15\n"
            )

    def test_index_in_sitemap(self):
        sitemap_path = os.path.join(self.target_dir, "output", "sitemap.xml")
        sitemap_data = codecs.open(sitemap_path, "r", "utf8").read()
        self.assertTrue('<loc>http://getnikola.com/index.html</loc>' in sitemap_data)

    def test_avoid_double_slash_in_rss(self):
        rss_path = os.path.join(self.target_dir, "output", "rss.xml")
        rss_data = codecs.open(rss_path, "r", "utf8").read()
        self.assertFalse('http://getnikola.com//' in rss_data)


class RepeatedPostsSetting(DemoBuildTest):
    """Duplicate POSTS, should not read each post twice, which causes conflicts."""
    @classmethod
    def patch_site(self):
        """Set the SITE_URL to have a path"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        with codecs.open(conf_path, "ab", "utf8") as outf:
            outf.write('\nPOSTS = (("posts/*.txt", "posts", "post.tmpl"),("posts/*.txt", "posts", "post.tmpl"))\n')


class FuturePostTest(EmptyBuildTest):
    """Test a site with future posts."""

    @classmethod
    def fill_site(self):
        import datetime
        from nikola.utils import current_time
        self.init_command.copy_sample_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)

        # Change COMMENT_SYSTEM_ID to not wait for 5 seconds
        with codecs.open(os.path.join(self.target_dir, 'conf.py'), "ab+", "utf8") as outf:
            outf.write('\nCOMMENT_SYSTEM_ID = "nikolatest"\n')

        with codecs.open(os.path.join(self.target_dir, 'posts', 'empty1.txt'), "wb+", "utf8") as outf:
            outf.write(
                ".. title: foo\n"
                ".. slug: foo\n"
                ".. date: %s\n" % (current_time() + datetime.timedelta(-1)).strftime('%Y-%m-%d %H:%M:%S')
            )

        with codecs.open(os.path.join(self.target_dir, 'posts', 'empty2.txt'), "wb+", "utf8") as outf:
            outf.write(
                ".. title: bar\n"
                ".. slug: bar\n"
                ".. date: %s\n" % (current_time() + datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')
            )

    def test_future_post(self):
        """ Ensure that the future post is not present in the index and sitemap."""
        index_path = os.path.join(self.target_dir, "output", "index.html")
        sitemap_path = os.path.join(self.target_dir, "output", "sitemap.xml")
        foo_path = os.path.join(self.target_dir, "output", "posts", "foo.html")
        bar_path = os.path.join(self.target_dir, "output", "posts", "bar.html")
        self.assertTrue(os.path.isfile(index_path))
        self.assertTrue(os.path.isfile(foo_path))
        self.assertTrue(os.path.isfile(bar_path))
        index_data = codecs.open(index_path, "r", "utf8").read()
        sitemap_data = codecs.open(sitemap_path, "r", "utf8").read()
        self.assertTrue('foo.html' in index_data)
        self.assertFalse('bar.html' in index_data)
        self.assertTrue('foo.html' in sitemap_data)
        self.assertFalse('bar.html' in sitemap_data)

        # Run deploy command to see if future post is deleted
        with cd(self.target_dir):
            __main__.main(["deploy"])

        self.assertTrue(os.path.isfile(index_path))
        self.assertTrue(os.path.isfile(foo_path))
        self.assertFalse(os.path.isfile(bar_path))


class TranslatedBuildTest(EmptyBuildTest):
    """Test a site with translated content."""

    dataname = "translated_titles"

    def __init__(self, *a, **kw):
        super(TranslatedBuildTest, self).__init__(*a, **kw)
        try:
            locale.setlocale(locale.LC_ALL, ("pl_PL", "utf8"))
        except:
            raise SkipTest

    def test_translated_titles(self):
        """Check that translated title is picked up."""
        en_file = os.path.join(self.target_dir, "output", "stories", "1.html")
        pl_file = os.path.join(self.target_dir, "output", "pl", "stories", "1.html")
        # Files should be created
        self.assertTrue(os.path.isfile(en_file))
        self.assertTrue(os.path.isfile(pl_file))
        # And now let's check the titles
        with codecs.open(en_file, 'r', 'utf8') as inf:
            doc = lxml.html.parse(inf)
            self.assertEqual(doc.find('//title').text, 'Foo | Demo Site')
        with codecs.open(pl_file, 'r', 'utf8') as inf:
            doc = lxml.html.parse(inf)
            self.assertEqual(doc.find('//title').text, 'Bar | Demo Site')


class TranslationsPatternTest1(TranslatedBuildTest):
    """Check that the path.lang.ext TRANSLATIONS_PATTERN works too"""

    @classmethod
    def patch_site(self):
        """Set the TRANSLATIONS_PATTERN to the new v7 default"""
        os.rename(os.path.join(self.target_dir, "stories", "1.txt.pl"),
                  os.path.join(self.target_dir, "stories", "1.pl.txt")
                  )
        conf_path = os.path.join(self.target_dir, "conf.py")
        with codecs.open(conf_path, "rb", "utf-8") as inf:
            data = inf.read()
            data = data.replace('TRANSLATIONS_PATTERN = "{path}.{ext}.{lang}"',
                                'TRANSLATIONS_PATTERN = "{path}.{lang}.{ext}"')
        with codecs.open(conf_path, "wb+", "utf8") as outf:
            outf.write(data)


class TranslationsPatternTest2(TranslatedBuildTest):
    """Check that the path_lang.ext TRANSLATIONS_PATTERN works too"""

    @classmethod
    def patch_site(self):
        """Set the TRANSLATIONS_PATTERN to the new v7 default"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        os.rename(os.path.join(self.target_dir, "stories", "1.txt.pl"),
                  os.path.join(self.target_dir, "stories", "1_pl.txt")
                  )
        with codecs.open(conf_path, "rb", "utf-8") as inf:
            data = inf.read()
            data = data.replace('TRANSLATIONS_PATTERN = "{path}.{ext}.{lang}"',
                                'TRANSLATIONS_PATTERN = "{path}_{lang}.{ext}"')
        with codecs.open(conf_path, "wb+", "utf8") as outf:
            outf.write(data)


class RelativeLinkTest(DemoBuildTest):
    """Check that SITE_URL with a path doesn't break links."""

    @classmethod
    def patch_site(self):
        """Set the SITE_URL to have a path"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        with codecs.open(conf_path, "rb", "utf-8") as inf:
            data = inf.read()
            data = data.replace('SITE_URL = "http://getnikola.com/"',
                                'SITE_URL = "http://getnikola.com/foo/bar/"')
        with codecs.open(conf_path, "wb+", "utf8") as outf:
            outf.write(data)

    def test_relative_links(self):
        """Check that the links in output/index.html are correct"""
        test_path = os.path.join(self.target_dir, "output", "index.html")
        flag = False
        with open(test_path, "rb") as inf:
            data = inf.read()
            for _, _, url, _ in lxml.html.iterlinks(data):
                # Just need to be sure this one is ok
                if url.endswith("css"):
                    self.assertFalse(url.startswith(".."))
                    flag = True
        # But I also need to be sure it is there!
        self.assertTrue(flag)

    def test_index_in_sitemap(self):
        """Test that the correct path is in sitemap, and not the wrong one."""
        sitemap_path = os.path.join(self.target_dir, "output", "sitemap.xml")
        sitemap_data = codecs.open(sitemap_path, "r", "utf8").read()
        self.assertFalse('<loc>http://getnikola.com/</loc>' in sitemap_data)
        self.assertTrue('<loc>http://getnikola.com/foo/bar/index.html</loc>' in sitemap_data)


class TestCheck(DemoBuildTest):
    """The demo build should pass 'nikola check'"""

    def test_check_links(self):
        with cd(self.target_dir):
            try:
                __main__.main(['check', '-l'])
            except SystemExit as e:
                self.assertEqual(e.code, 0)

    def test_check_files(self):
        with cd(self.target_dir):
            try:
                __main__.main(['check', '-f'])
            except SystemExit as e:
                self.assertEqual(e.code, 0)


class TestCheckFailure(DemoBuildTest):
    """The demo build should pass 'nikola check'"""

    def test_check_links_fail(self):
        with cd(self.target_dir):
            os.unlink(os.path.join("output", "archive.html"))
            try:
                __main__.main(['check', '-l'])
            except SystemExit as e:
                self.assertNotEqual(e.code, 0)

    def test_check_files_fail(self):
        with cd(self.target_dir):
            with codecs.open(os.path.join("output", "foobar"), "wb+", "utf8") as outf:
                outf.write("foo")
            try:
                __main__.main(['check', '-f'])
            except SystemExit as e:
                self.assertNotEqual(e.code, 0)


class RelativeLinkTest2(DemoBuildTest):
    """Check that dropping stories to the root doesn't break links."""

    @classmethod
    def patch_site(self):
        """Set the SITE_URL to have a path"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        with codecs.open(conf_path, "rb", "utf-8") as inf:
            data = inf.read()
            data = data.replace('("stories/*.txt", "stories", "story.tmpl"),',
                                '("stories/*.txt", "", "story.tmpl"),')
            data = data.replace('("stories/*.rst", "stories", "story.tmpl"),',
                                '("stories/*.rst", "", "story.tmpl"),')
            data = data.replace('# INDEX_PATH = ""',
                                'INDEX_PATH = "blog"')
        with codecs.open(conf_path, "wb+", "utf8") as outf:
            outf.write(data)
            outf.flush()

    def test_relative_links(self):
        """Check that the links in a story are correct"""
        test_path = os.path.join(self.target_dir, "output", "about-nikola.html")
        flag = False
        with open(test_path, "rb") as inf:
            data = inf.read()
            for _, _, url, _ in lxml.html.iterlinks(data):
                # Just need to be sure this one is ok
                if url.endswith("css"):
                    self.assertFalse(url.startswith(".."))
                    flag = True
        # But I also need to be sure it is there!
        self.assertTrue(flag)

    def test_index_in_sitemap(self):
        """Test that the correct path is in sitemap, and not the wrong one."""
        sitemap_path = os.path.join(self.target_dir, "output", "sitemap.xml")
        sitemap_data = codecs.open(sitemap_path, "r", "utf8").read()
        self.assertFalse('<loc>http://getnikola.com/</loc>' in sitemap_data)
        self.assertTrue('<loc>http://getnikola.com/blog/index.html</loc>' in sitemap_data)


class MonthlyArchiveTest(DemoBuildTest):
    """Check that the monthly archives build and are correct."""

    @classmethod
    def patch_site(self):
        """Set the SITE_URL to have a path"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        with codecs.open(conf_path, "rb", "utf-8") as inf:
            data = inf.read()
            data = data.replace('# CREATE_MONTHLY_ARCHIVE = False',
                                'CREATE_MONTHLY_ARCHIVE = True')
        with codecs.open(conf_path, "wb+", "utf8") as outf:
            outf.write(data)
            outf.flush()

    def test_monthly_archive(self):
        """See that it builds"""
        self.assertTrue(os.path.isfile(os.path.join(self.tmpdir, 'target', 'output', '2012', '03', 'index.html')))


class SubdirRunningTest(DemoBuildTest):
    """Check that running nikola from subdir works."""

    def test_subdir_run(self):
        """Check whether build works from posts/"""

        with cd(os.path.join(self.target_dir, 'posts')):
            result = __main__.main(['build'])
            self.assertEquals(result, 0)


if __name__ == "__main__":
    unittest.main()
