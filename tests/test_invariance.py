# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

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

from nikola import main
import nikola
import nikola.plugins.command
import nikola.plugins.command.init

from test_integration import DemoBuildTest, cd

class InvariantBuildTest(DemoBuildTest):
    """Test that a default build of --demo works."""

    def test_invariance(self):
        """Compare the output to the canonical output."""
        good_path = os.path.join(os.path.dirname(__file__), 'data', 'invariant')
        with cd(self.target_dir):
            diff = subprocess.check_output(['diff', '-r', good_path, 'output'])
            self.assertEqual(diff.strip(), '')

if __name__ == "__main__":
    unittest.main()
