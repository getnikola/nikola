# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import sys


import unittest


class ImportPluginsTest(unittest.TestCase):
    def test_importing_command_import_wordpress(self):
        import nikola.plugins.command.import_wordpress  # NOQA

    def test_importing_compile_rest(self):
        import nikola.plugins.compile.rest  # NOQA

    def test_importing_plugin_compile_markdown(self):
        import nikola.plugins.compile.markdown    # NOQA
