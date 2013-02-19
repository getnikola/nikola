# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from contextlib import contextmanager
import os
import shutil
import tempfile
import unittest

from context import nikola


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)


class IntegrationTest(unittest.TestCase):
    """Basic integration testcase."""
    def setUp(self):
        """Setup a demo site."""
        self.tmpdir = tempfile.mkdtemp()
        self.target_dir = os.path.join(self.tmpdir, "target")
        self.build_command = nikola.plugins.command_build.CommandBuild()
        self.init_command = nikola.plugins.command_init.CommandInit()
        self.init_command.copy_sample_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)
        self.patch_site()
        self.build()

    def patch_site(self):
        """Make any modifications you need to the site."""
        pass

    def build(self):
        """Build the site."""
        with cd(self.target_dir):
            self.build_command.run()

    def tearDown(self):
        """Reove the demo site."""
        shutil.rmtree(self.tmpdir)


class EmptytBuild(IntegrationTest):
    """Basic integration testcase."""
    def setUp(self):
        """Setup a demo site."""
        self.tmpdir = tempfile.mkdtemp()
        self.target_dir = os.path.join(self.tmpdir, "target")
        self.build_command = nikola.plugins.command_build.CommandBuild()
        self.init_command = nikola.plugins.command_init.CommandInit()
        self.init_command.create_empty_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)
        self.patch_site()
        self.build()

    def test_deleted_dodo(self):
        """Test that a default build of --demo works."""
        # Ensure the temprary dodo file is deleted (Issue #302)
        self.assertFalse(os.path.isfile(self.build_command.dodo.name))


class DefaultBuild(IntegrationTest):
    """Test that a default build of --demo works."""

    def test_deleted_dodo(self):
        """Test that a default build of --demo works."""
        # Ensure the temprary dodo file is deleted (Issue #302)
        self.assertFalse(os.path.isfile(self.build_command.dodo.name))
