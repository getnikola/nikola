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


#class TestCheck(DemoBuildTest):
    #"""The demo build should pass 'nikola check'"""

    #def test_check_links(self):
        #with cd(self.target_dir):
            #p = subprocess.Popen(
                #"nikola check -l", shell=True, stdout=subprocess.PIPE,
                #stderr=subprocess.PIPE)
            #out, err = p.communicate()
            #sys.stdout.write(out)
            #sys.stderr.write(err)
        #self.assertEqual(p.returncode, 0)

    #def test_check_files(self):
        #with cd(self.target_dir):
            #p = subprocess.Popen(
                #"nikola check -f", shell=True, stdout=subprocess.PIPE,
                #stderr=subprocess.PIPE)
            #out, err = p.communicate()
            #sys.stdout.write(out)
            #sys.stderr.write(err)
        #import pdb; pdb.set_trace()
        #self.assertEqual(p.returncode, 0)


#class TestCheckFailure(DemoBuildTest):
    #"""The demo build should pass 'nikola check'"""

    #def test_check_links_fail(self):
        #with cd(self.target_dir):
            #os.unlink(os.path.join("output", "archive.html"))
            #p = subprocess.Popen(
                #"nikola check -l", shell=True, stdout=subprocess.PIPE,
                #stderr=subprocess.PIPE)
            #out, err = p.communicate()
            #sys.stdout.write(out)
            #sys.stderr.write(err)
        #self.assertEqual(p.returncode, 1)

    #def test_check_files_fail(self):
        #with cd(self.target_dir):
            #with codecs.open(os.path.join("output", "foobar"), "wb+", "utf8") as outf:
                #outf.write("foo")
            #p = subprocess.Popen(
                #"nikola check -f", shell=True, stdout=subprocess.PIPE,
                #stderr=subprocess.PIPE)
            #out, err = p.communicate()
            #sys.stdout.write(out)
            #sys.stderr.write(err)
        #self.assertEqual(p.returncode, 1)


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
