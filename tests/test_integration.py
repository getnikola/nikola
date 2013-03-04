# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

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

    def patch_site(self):
        """Make any modifications you need to the site."""

    def build(self):
        """Build the site."""
        with cd(self.target_dir):
            main.main(["build"])

    def tearDown(self):
        """Remove the demo site."""
        #shutil.rmtree(self.tmpdir)

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

class RelativeLinkTest(DemoBuildTest):
    """Check that SITE_URL with a path doesn't break links."""

    def patch_site(self):
        """Set the SITE_URL to have a path"""
        conf_path = os.path.join(self.target_dir, "conf.py")
        with open(conf_path, "rb") as inf:
            data = inf.read()
            data = data.replace('SITE_URL = "http://nikola.ralsina.com.ar"',
                                'SITE_URL = "http://nikola.ralsina.com.ar/foo/bar/"')
        with open(conf_path, "wb+") as outf:
            outf.write(data)

    def test_relative_links(self):
        """Check that the links in output/index.html are correct"""
        test_path = os.path.join(self.target_dir, "output", "index.html")
        flag = False
        with open(test_path, "rb") as inf:
            data = inf.read()
            for _, _, url, _ in lxml.html.iterlinks(data):
                # Just need to be sure this one is ok
                if "assets/css/all-nocdn.css" in url:
                    self.assertEqual(url, 'assets/css/all-nocdn.css')
                    flag = True
        # But I also need to be sure it is there!
        self.assertTrue(flag)
