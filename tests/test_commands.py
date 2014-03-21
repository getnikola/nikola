# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

# This code is so you can run the samples without installing the package,
# and should be before any import touching nikola, in any file under tests/
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from nikola.plugins.command.version import CommandVersion


class CommandVersionCallTest(unittest.TestCase):
    def test_version(self):
        """Test `nikola version`."""
        CommandVersion().execute()
