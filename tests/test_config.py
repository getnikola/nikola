import os
import re

import pytest

from nikola import __main__ as nikola


def test_simple_config(simple_config, metadata_option):
    """Check whether configuration-files without ineritance are interpreted correctly."""
    assert simple_config[metadata_option]["ID"] == "conf"


def test_inherited_config(simple_config, metadata_option, complex_config):
    """Check whether configuration-files with ineritance are interpreted correctly."""
    check_base_equality(simple_config, metadata_option, complex_config)
    assert complex_config[metadata_option]["ID"] == "prod"


def test_config_with_illegal_filename(
    simple_config, metadata_option, complex_filename_config
):
    """Check whether files with illegal module-name characters can be set as config-files, too."""
    check_base_equality(simple_config, metadata_option, complex_filename_config)
    assert complex_filename_config[metadata_option]["ID"] == "illegal"


@pytest.fixture(scope="module")
def simple_config(data_dir):
    nikola.main(["--conf=" + os.path.join(data_dir, "conf.py")])
    return nikola.config


@pytest.fixture(scope="module")
def data_dir(test_dir):
    return os.path.join(test_dir, "data", "test_config")


@pytest.fixture
def metadata_option():
    return "ADDITIONAL_METADATA"


@pytest.fixture(scope="module")
def complex_config(data_dir):
    nikola.main(["--conf=" + os.path.join(data_dir, "prod.py")])
    return nikola.config


@pytest.fixture(scope="module")
def complex_filename_config(data_dir):
    config_path = os.path.join(
        data_dir, "config.with+illegal(module)name.characters.py"
    )
    nikola.main(["--conf=" + config_path])
    return nikola.config


def check_base_equality(base_config, metadata_option, config):
    """Check whether the specified `config` equals the base config."""
    for option in base_config.keys():
        if re.match("^[A-Z]+(_[A-Z]+)*$", option) and option != metadata_option:
            assert base_config[option] == config[option]
