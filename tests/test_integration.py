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

    def tearDown(self):
        """Reove the demo site."""
        shutil.rmtree(self.tmpdir)

    def test_default_build(self):
        """Test that a default build of --demo works."""
        with cd(self.target_dir):
            self.build_command.run()
            self.assertTrue(True)  # Meaning we did not crash ;-)
