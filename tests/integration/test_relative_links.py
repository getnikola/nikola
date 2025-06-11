"""Check that SITE_URL with a path doesn't break links."""

from pathlib import Path

import lxml.html
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


def test_relative_links(build, output_dir):
    """Check that the links in output/index.html are correct"""
    test_path = Path(output_dir) / "index.html"

    data = test_path.read_bytes()

    assert not any(
        url.startswith("..")
        for _, _, url, _ in lxml.html.fromstring(data).iterlinks()
        if url.endswith("css")
    )


def test_index_in_sitemap(build, output_dir):
    """Test that the correct path is in sitemap, and not the wrong one."""
    sitemap_path = Path(output_dir) / "sitemap.xml"
    sitemap_data = sitemap_path.read_text(encoding="utf8")

    assert "<loc>https://example.com/</loc>" not in sitemap_data
    assert "<loc>https://example.com/foo/bar/</loc>" in sitemap_data


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    # Set the SITE_URL to have a path with subfolder
    patch_config(
        target_dir,
        (
            'SITE_URL = "https://example.com/"',
            'SITE_URL = "https://example.com/foo/bar/"',
        ),
    )

    with cd(target_dir):
        __main__.main(["build"])
