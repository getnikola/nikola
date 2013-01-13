# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from context import nikola
import unittest


class ImportPluginsTest(unittest.TestCase):
    def test_importing_command_import_wordpress(self):
        import nikola.plugins.command_import_wordpress

    def test_importing_task_sitemap(self):
        import nikola.plugins.task_sitemap.sitemap_gen

    def test_importing_compile_rest(self):
        import nikola.plugins.compile_rest