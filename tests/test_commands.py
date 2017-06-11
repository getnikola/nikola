# -*- coding: utf-8 -*-

import unittest

from nikola.plugins.command.version import CommandVersion


class CommandVersionCallTest(unittest.TestCase):
    def test_version(self):
        """Test `nikola version`."""
        CommandVersion().execute()
