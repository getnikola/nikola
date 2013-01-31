# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from context import nikola
import os
import unittest
import mock


class CommandInitCallTest(unittest.TestCase):
    def setUp(self):
        self.copy_sample_site = mock.MagicMock()
        self.create_configuration = mock.MagicMock()
        self.create_empty_site = mock.MagicMock()
        copy_sample_site_patch = mock.patch(
            'nikola.plugins.command_init.CommandInit.copy_sample_site', self.copy_sample_site)
        create_configuration_patch = mock.patch(
            'nikola.plugins.command_init.CommandInit.create_configuration', self.create_configuration)
        create_empty_site_patch = mock.patch(
            'nikola.plugins.command_init.CommandInit.create_empty_site', self.create_empty_site)

        self.patches = [copy_sample_site_patch,
                        create_configuration_patch, create_empty_site_patch]
        for patch in self.patches:
            patch.start()

        self.init_commad = nikola.plugins.command_init.CommandInit()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        del self.patches

        del self.copy_sample_site
        del self.create_configuration
        del self.create_empty_site

    def test_init_default(self):
        for arguments in (('destination', '--demo'),):
            self.init_commad.run(*arguments)

            self.assertTrue(self.create_configuration.called)
            self.assertTrue(self.copy_sample_site.called)
            self.assertFalse(self.create_empty_site.called)

    def test_init_called_without_target(self):
        self.init_commad.run()

        self.assertFalse(self.create_configuration.called)
        self.assertFalse(self.copy_sample_site.called)
        self.assertFalse(self.create_empty_site.called)

    def test_init_empty_dir(self):
        for arguments in (('destination', ), ('destination', '--empty')):
            self.init_commad.run(*arguments)

            self.assertTrue(self.create_configuration.called)
            self.assertFalse(self.copy_sample_site.called)
            self.assertTrue(self.create_empty_site.called)


if __name__ == '__main__':
    unittest.main()
