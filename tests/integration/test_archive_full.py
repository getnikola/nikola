"""Check that full archives build and are correct."""

import os

import pytest

from nikola import __main__

from .helper import cd, patch_config
from .test_demo_build import prepare_demo_site
from .test_empty_build import (  # NOQA
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(["archive.html"], id="overall"),
        pytest.param(["2012", "index.html"], id="year"),
        pytest.param(["2012", "03", "index.html"], id="month"),
        pytest.param(["2012", "03", "30", "index.html"], id="day"),
    ],
)
def test_full_archive(build, output_dir, path):
    """Check existance of archive pages"""
    expected_path = os.path.join(output_dir, *path)
    assert os.path.isfile(expected_path)


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    patch_config(
        target_dir, ("# CREATE_FULL_ARCHIVES = False", "CREATE_FULL_ARCHIVES = True")
    )

    with cd(target_dir):
        __main__.main(["build"])
