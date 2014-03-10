# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

# This code is so you can run the samples without installing the package,
# and should be before any import touching nikola, in any file under tests/
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


import unittest


class ImportPluginsTest(unittest.TestCase):
    def test_importing_command_import_wordpress(self):
        import nikola.plugins.command.import_wordpress  # NOQA

    def test_importing_compile_rest(self):
        import nikola.plugins.compile.rest  # NOQA

    def test_importing_plugin_compile_markdown(self):
        import nikola.plugins.compile.markdown    # NOQA
