# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import codecs
from contextlib import contextmanager
import locale
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import lxml.html
from nose.plugins.skip import SkipTest

from context import nikola
from nikola import main


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)


class EmptyBuildTest(unittest.TestCase):
    """Basic integration testcase."""

    dataname = None

    def setUp(self):
        """Setup a demo site."""
        self.tmpdir = tempfile.mkdtemp()
        self.target_dir = os.path.join(self.tmpdir, "target")
        self.init_command = nikola.plugins.command_init.CommandInit()
        self.fill_site()
        self.patch_site()
        self.build()

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

    def patch_site(self):
        """Make any modifications you need to the site."""

    def build(self):
        """Build the site."""
        with cd(self.target_dir):
            main.main(["build"])

    def tearDown(self):
        """Remove the demo site."""
        shutil.rmtree(self.tmpdir)
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

    def fill_site(self):
        """Fill the site with demo content."""
        self.init_command.copy_sample_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)
        # File for Issue #374 (empty post text)
        with codecs.open(os.path.join(self.target_dir, 'posts', 'empty.txt'), "wb+", "utf8") as outf:
            outf.write(
                ".. title: foobar\n"
                ".. slug: foobar\n"
                ".. date: 2013/03/06 19:08:15\n"
            )

    def test_index_in_sitemap(self):
        sitemap_path = os.path.join(self.target_dir, "output", "sitemap.xml")
        sitemap_data = codecs.open(sitemap_path, "r", "utf8").read()
        self.assertTrue('<loc>http://nikola.ralsina.com.ar/</loc>' in sitemap_data)

class FuturePostTest(DemoBuildTest):
    """Test a site with future posts."""

    def fill_site(self):
        import datetime
        from nikola.utils import current_time
        self.init_command.copy_sample_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)
        with codecs.open(os.path.join(self.target_dir, 'posts', 'empty1.txt'), "wb+", "utf8") as outf:
            outf.write(
                ".. title: foo\n"
                ".. slug: foo\n"
                ".. date: %s\n" % (current_time() + datetime.timedelta(-1)).strftime('%Y/%m/%d %T')
            )

        with codecs.open(os.path.join(self.target_dir, 'posts', 'empty2.txt'), "wb+", "utf8") as outf:
            outf.write(
                ".. title: bar\n"
                ".. slug: bar\n"
                ".. date: %s\n" % (current_time() + datetime.timedelta(1)).strftime('%Y/%m/%d %T')
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


class TranslatedBuildTest(EmptyBuildTest):
    """Test a site with translated content."""

    dataname = "translated_titles"

    def __init__(self, *a, **kw):
        super(TranslatedBuildTest, self).__init__(*a, **kw)
        try:
            locale.setlocale(locale.LC_ALL, ("es", "utf8"))
        except:
            raise SkipTest

    def test_translated_titles(self):
        """Check that translated title is picked up."""
        en_file = os.path.join(self.target_dir, "output", "stories", "1.html")
        es_file = os.path.join(self.target_dir, "output", "es", "stories", "1.html")
        # Files should be created
        self.assertTrue(os.path.isfile(en_file))
        self.assertTrue(os.path.isfile(es_file))
        # And now let's check the titles
        with codecs.open(en_file, 'r', 'utf8') as inf:
            doc = lxml.html.parse(inf)
            self.assertEqual(doc.find('//title').text, 'Foo | Demo Site')
        with codecs.open(es_file, 'r', 'utf8') as inf:
            doc = lxml.html.parse(inf)
            self.assertEqual(doc.find('//title').text, 'Bar | Demo Site')


class RelativeLinkTest(DemoBuildTest):
    """Check that SITE_URL with a path doesn't break links."""

    def patch_site(self):
        """Set the SITE_URL to have a path"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        with codecs.open(conf_path, "rb", "utf-8") as inf:
            data = inf.read()
            data = data.replace('SITE_URL = "http://nikola.ralsina.com.ar"',
                                'SITE_URL = "http://nikola.ralsina.com.ar/foo/bar/"')
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
        self.assertFalse('<loc>http://nikola.ralsina.com.ar/</loc>' in sitemap_data)
        self.assertTrue('<loc>http://nikola.ralsina.com.ar/foo/bar/</loc>' in sitemap_data)


class TestCheck(DemoBuildTest):
    """The demo build should pass 'nikola check'"""

    def test_check_links(self):
        with cd(self.target_dir):
            p = subprocess.call("nikola check -l", shell=True)
        self.assertEqual(p, 0)

    def test_check_files(self):
        with cd(self.target_dir):
            p = subprocess.call("nikola check -f", shell=True)
        self.assertEqual(p, 0)


class TestCheckFailure(DemoBuildTest):
    """The demo build should pass 'nikola check'"""

    def test_check_links_fail(self):
        with cd(self.target_dir):
            os.unlink(os.path.join("output", "archive.html"))
            p = subprocess.call("nikola check -l", shell=True)
        self.assertEqual(p, 1)

    def test_check_files_fail(self):
        with cd(self.target_dir):
            with codecs.open(os.path.join("output", "foobar"), "wb+", "utf8") as outf:
                outf.write("foo")
            p = subprocess.call("nikola check -f", shell=True)
        self.assertEqual(p, 1)


class RelativeLinkTest2(DemoBuildTest):
    """Check that dropping stories to the root doesn't break links."""

    def patch_site(self):
        """Set the SITE_URL to have a path"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        with codecs.open(conf_path, "rb", "utf-8") as inf:
            data = inf.read()
            data = data.replace('("stories/*.txt", "stories", "story.tmpl", False),',
                                '("stories/*.txt", "", "story.tmpl", False),')
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
        self.assertFalse('<loc>http://nikola.ralsina.com.ar/</loc>' in sitemap_data)
        self.assertTrue('<loc>http://nikola.ralsina.com.ar/blog/</loc>' in sitemap_data)

