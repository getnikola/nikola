# -*- coding: utf-8 -*-
import os
import re

from nikola import __main__ as nikola

from .base import BaseTestCase


class ConfigTest(BaseTestCase):
    """Provides tests for the configuration-file handling."""
    @classmethod
    def setUpClass(self):
        self.metadata_option = "ADDITIONAL_METADATA"
        script_root = os.path.dirname(__file__)
        test_dir = os.path.join(script_root, "data", "test_config")
        nikola.main(["--conf=" + os.path.join(test_dir, "conf.py")])
        self.simple_config = nikola.config
        nikola.main(["--conf=" + os.path.join(test_dir, "prod.py")])
        self.complex_config = nikola.config
        nikola.main(["--conf=" + os.path.join(test_dir, "config.with+illegal(module)name.characters.py")])
        self.complex_filename_config = nikola.config
        self.check_base_equality(self.complex_filename_config)

    @classmethod
    def check_base_equality(self, config):
        """Check whether the specified `config` equals the base config."""
        for option in self.simple_config.keys():
            if re.match("^[A-Z]+(_[A-Z]+)*$", option) and option != self.metadata_option:
                assert self.simple_config[option] == config[option]

    def test_simple_config(self):
        """Check whether configuration-files without ineritance are interpreted correctly."""
        assert self.simple_config[self.metadata_option]["ID"] == "conf"

    def test_inherited_config(self):
        """Check whether configuration-files with ineritance are interpreted correctly."""
        self.check_base_equality(config=self.complex_config)
        assert self.complex_config[self.metadata_option]["ID"] == "prod"

    def test_config_with_illegal_filename(self):
        """Check whether files with illegal module-name characters can be set as config-files, too."""
        self.check_base_equality(config=self.complex_filename_config)
        assert self.complex_filename_config[self.metadata_option]["ID"] == "illegal"
