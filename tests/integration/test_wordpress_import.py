# -*- coding: utf-8 -*-
"""
Testing the wordpress import.

It will do create a new site with the import_wordpress command
and use that newly created site to make a build.
"""

import os.path
from glob import glob

import pytest

from nikola import __main__

from .helper import cd
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
)


def test_import_created_files(build, target_dir):
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, "conf.py"))


@pytest.mark.parametrize("dirname", ["pages", "posts"])
def test_filled_directories(build, target_dir, dirname):
    folder = os.path.join(target_dir, dirname)
    assert os.path.isdir(folder)
    content = glob(os.path.join(folder, "**"), recursive=True)
    assert any(os.path.isfile(element) for element in content)


@pytest.fixture(scope="module")
def build(target_dir, import_file):
    __main__.main(
        [
            "import_wordpress",
            "--no-downloads",
            "--output-folder",
            target_dir,
            import_file,
        ]
    )

    with cd(target_dir):
        result = __main__.main(["build"])
        assert not result


@pytest.fixture(scope="module")
def import_file(test_dir):
    """Path to the Wordpress export file."""
    return os.path.join(
        test_dir, "..", "data", "wordpress_import", "wordpress_export_example.xml"
    )
