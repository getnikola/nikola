"""Check that dropping pages to the root doesn't break links."""

import io
import os

import lxml
import pytest

from nikola import __main__

from .helper import append_config, cd, patch_config
from .test_demo_build import prepare_demo_site
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
)


def test_relative_links(build, output_dir):
    """Check that the links in a page are correct"""
    test_path = os.path.join(output_dir, "about-nikola.html")

    with io.open(test_path, "rb") as inf:
        data = inf.read()

    assert not any(
        url.startswith("..")
        for _, _, url, _ in lxml.html.iterlinks(data)
        if url.endswith("css")
    )


def test_index_in_sitemap(build, output_dir):
    """Test that the correct path is in sitemap, and not the wrong one."""
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with io.open(sitemap_path, "r", encoding="utf8") as inf:
        sitemap_data = inf.read()

    assert "<loc>https://example.com/</loc>" not in sitemap_data
    assert "<loc>https://example.com/blog/index.html</loc>" in sitemap_data


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    # Configure our pages to reside in the root
    patch_config(
        target_dir,
        ('("pages/*.txt", "pages", "page.tmpl"),', '("pages/*.txt", "", "page.tmpl"),'),
        ('("pages/*.rst", "pages", "page.tmpl"),', '("pages/*.rst", "", "page.tmpl"),'),
        ('# INDEX_PATH = ""', 'INDEX_PATH = "blog"'),
    )
    append_config(
        target_dir,
        """
PRETTY_URLS = False
STRIP_INDEXES = False
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
