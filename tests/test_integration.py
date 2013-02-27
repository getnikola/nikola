# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from contextlib import contextmanager
import os
import tempfile
import unittest

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
            main.main([])

    def tearDown(self):
        """Reove the demo site."""
        #shutil.rmtree(self.tmpdir)

    def test_build(self):
        self.assertTrue(True)


class DemoBuildTest(EmptyBuildTest):
    """Test that a default build of --demo works."""

    def fill_site(self):
        """Fill the site with demo content."""
        self.init_command.copy_sample_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)
