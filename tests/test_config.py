# -*- coding: utf-8 -*-
import os
import random
import re

import unittest
from nikola import __main__ as nikola

from .base import BaseTestCase


class ConfigTest(BaseTestCase):
    """Provides tests for the configuration-file handling."""
    def setUp(self):
        script_root = os.path.dirname(__file__)
        test_dir = os.path.join(script_root, "data", "test_config")
        nikola.main(["--conf=" + os.path.join(test_dir, "conf.py")])
        self.simple_config = nikola.config
        nikola.main(["--conf=" + os.path.join(test_dir, "prod.py")])
        self.complex_config = nikola.config

        options = list()
        for option in self.simple_config.keys():
            if re.match("^[A-Z]+(_[A-Z]+)*$", option) and option != "ADDITIONAL_METADATA":
                options.append(option)
        self.option = random.choice(options)

    def test_simple_config(self):
        """Checks whether configuration-files without ineritance are interpreted correctly."""
        assert self.simple_config["ADDITIONAL_METADATA"]["ID"] == "conf"

    def test_inherited_config(self):
        """Checks whether configuration-files with ineritance areinterpreted correctly."""
        assert self.simple_config[self.option] == self.complex_config[self.option]
        assert self.complex_config["ADDITIONAL_METADATA"]["ID"] == "prod"


if __name__ == '__main__':
    unittest.main()
