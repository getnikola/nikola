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
        copy_sample_site_patch = mock.patch('nikola.plugins.command_init.CommandInit.copy_sample_site', self.copy_sample_site)
        create_configuration_patch = mock.patch('nikola.plugins.command_init.CommandInit.create_configuration', self.create_configuration)

        self.patches = [copy_sample_site_patch, create_configuration_patch]
        for patch in self.patches:
            patch.start()

        self.init_commad = nikola.plugins.command_init.CommandInit()

    def tearDown(self):
        del self.copy_sample_site
        del self.create_configuration

        for patch in self.patches:
            patch.stop()
        del self.patches

    def test_init_default(self):
        self.init_commad.run('destination')

        self.assertTrue(self.create_configuration.called)
        self.assertTrue(self.copy_sample_site.called)

