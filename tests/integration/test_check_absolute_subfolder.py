"""
Validate links in a site which is:

* built in URL_TYPE="absolute"
* deployable to a subfolder (BASE_URL="https://example.com/foo/")
"""

import io
import os

import pytest

from nikola import __main__

from .helper import cd, patch_config
from .test_demo_build import prepare_demo_site
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
)


def test_index_in_sitemap(build, output_dir):
    """
    Test that the correct path is in sitemap, and not the wrong one.

    The correct path ends in /foo/ because this is where we deploy to.
    """
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with io.open(sitemap_path, "r", encoding="utf8") as inf:
        sitemap_data = inf.read()

    assert "<loc>https://example.com/foo/</loc>" in sitemap_data


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    patch_config(
        target_dir,
        ('SITE_URL = "https://example.com/"', 'SITE_URL = "https://example.com/foo/"'),
        ("# URL_TYPE = 'rel_path'", "URL_TYPE = 'absolute'"),
    )

    with cd(target_dir):
        __main__.main(["build"])
