# -*- coding: utf-8 -*-
"""
Testing the wordpress import.

It will do create a new site with the import_wordpress command
and use that newly created site to make a build.
"""

import os
import os.path

import pytest

from nikola import __main__

from ..base import cd


def test_import_created_files(build, target_dir):
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, 'conf.py'))

    pages = os.path.join(target_dir, 'pages')
    assert os.path.isdir(pages)


@pytest.fixture(scope="module")
def build(target_dir, import_file):
    __main__.main(["import_wordpress",
                   "--no-downloads",
                   "--output-folder", target_dir,
                   import_file])

    with cd(target_dir):
        result = __main__.main(["build"])
        assert not result


@pytest.fixture(scope="module")
def import_file():
    """Path to the Wordpress export file."""
    test_directory = os.path.dirname(__file__)
    return os.path.join(test_directory, '..', 'wordpress_export_example.xml')
