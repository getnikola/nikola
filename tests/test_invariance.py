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

from test_integration import DemoBuildTest

class InvariantBuildTest(DemoBuildTest):
    """Test that a default build of --demo works."""

if __name__ == "__main__":
    unittest.main()
