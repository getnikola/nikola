# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import sys

import unittest

from nikola.plugins.command.version import CommandVersion


class CommandVersionCallTest(unittest.TestCase):
    def test_version(self):
        """Test `nikola version`."""
        CommandVersion().execute()
