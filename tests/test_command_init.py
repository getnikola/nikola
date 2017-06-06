# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import unittest
import mock

import nikola
from nikola.plugins.command.init import SAMPLE_CONF
from nikola.plugins.command.init import format_default_translations_config


class CommandInitCallTest(unittest.TestCase):
    def setUp(self):
        self.ask_questions = mock.MagicMock()
        self.copy_sample_site = mock.MagicMock()
        self.create_configuration = mock.MagicMock()
        self.create_empty_site = mock.MagicMock()
        ask_questions_patch = mock.patch(
            'nikola.plugins.command.init.CommandInit.ask_questions', self.ask_questions)
        copy_sample_site_patch = mock.patch(
            'nikola.plugins.command.init.CommandInit.copy_sample_site', self.copy_sample_site)
        create_configuration_patch = mock.patch(
            'nikola.plugins.command.init.CommandInit.create_configuration',
            self.create_configuration)
        create_empty_site_patch = mock.patch(
            'nikola.plugins.command.init.CommandInit.create_empty_site', self.create_empty_site)

        self.patches = [ask_questions_patch, copy_sample_site_patch,
                        create_configuration_patch, create_empty_site_patch]
        for patch in self.patches:
            patch.start()

        self.init_command = nikola.plugins.command.init.CommandInit()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        del self.patches

        del self.copy_sample_site
        del self.create_configuration
        del self.create_empty_site

    def test_init_default(self):
        self.init_command.execute()

        self.assertTrue(self.ask_questions.called)
        self.assertTrue(self.create_configuration.called)
        self.assertFalse(self.copy_sample_site.called)
        self.assertTrue(self.create_empty_site.called)

    def test_init_args(self):
        arguments = dict(
            options={'demo': True, 'quiet': True},
            args=['destination'])
        self.init_command.execute(**arguments)

        self.assertFalse(self.ask_questions.called)
        self.assertTrue(self.create_configuration.called)
        self.assertTrue(self.copy_sample_site.called)
        self.assertFalse(self.create_empty_site.called)

    def test_init_called_without_target_quiet(self):
        self.init_command.execute(**dict(options={'quiet': True}))

        self.assertFalse(self.ask_questions.called)
        self.assertFalse(self.create_configuration.called)
        self.assertFalse(self.copy_sample_site.called)
        self.assertFalse(self.create_empty_site.called)

    def test_init_empty_dir(self):
        self.init_command.execute(args=['destination'])

        self.assertTrue(self.ask_questions.called)
        self.assertTrue(self.create_configuration.called)
        self.assertFalse(self.copy_sample_site.called)
        self.assertTrue(self.create_empty_site.called)


class InitHelperTests(unittest.TestCase):
    """Test helper functions provided with the init command."""

    def test_configure_translations_without_additional_languages(self):
        """
        Testing the configuration of the translation when no additional language has been found.
        """
        translations_cfg = format_default_translations_config(set())
        self.assertEqual(SAMPLE_CONF["TRANSLATIONS"], translations_cfg)

    def test_configure_translations_with_2_additional_languages(self):
        """
        Testing the configuration of the translation when no additional language has been found.
        """
        translations_cfg = format_default_translations_config(
            set(["es", "en"]))
        self.assertEqual("""{
    DEFAULT_LANG: "",
    "en": "./en",
    "es": "./es",
}""", translations_cfg)


if __name__ == '__main__':
    unittest.main()
