# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import codecs
from contextlib import contextmanager
import os
import shutil
import tempfile
import unittest

import lxml.html

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
    @classmethod
    def setUpClass(self):
        """Setup a demo site."""
        self.tmpdir = tempfile.mkdtemp()
        self.target_dir = os.path.join(self.tmpdir, "target")
        self.init_command = nikola.plugins.command_init.CommandInit()
        self.fill_site()
        self.patch_site()
        self.build()

    @classmethod
    def fill_site(self):
        """Add any needed initial content."""
        self.init_command.create_empty_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)

    @classmethod
    def patch_site(self):
        """Make any modifications you need to the site."""

    @classmethod
    def build(self):
        """Build the site."""
        with cd(self.target_dir):
            main.main(["build"])

    @classmethod
    def tearDownClass(self):
        """Remove the demo site."""
        shutil.rmtree(self.tmpdir)

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


class RelativeLinkTest(DemoBuildTest):
    """Check that SITE_URL with a path doesn't break links."""

    @classmethod
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


@unittest.expectedFailure
class RelativeLinkTest2(DemoBuildTest):
    """Check that dropping stories to the root doesn't break links."""

    @classmethod
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
        conf_path = os.path.join(self.target_dir, "conf.py")
        data = open(conf_path).read()
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
