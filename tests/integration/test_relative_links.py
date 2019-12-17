"""Check that SITE_URL with a path doesn't break links."""

import io
import os
import shutil

import lxml
import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import add_post_without_text, cd, patch_config
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
)


def test_relative_links(build, output_dir):
    """Check that the links in output/index.html are correct"""
    test_path = os.path.join(output_dir, "index.html")

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
    assert "<loc>https://example.com/foo/bar/</loc>" in sitemap_data


@pytest.fixture(scope="module")
def build(target_dir, test_dir):
    """Fill the site with demo content and build it."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.copy_sample_site(target_dir)
    init_command.create_configuration(target_dir)

    src1 = os.path.join(test_dir, "..", "data", "1-nolinks.rst")
    dst1 = os.path.join(target_dir, "posts", "1.rst")
    shutil.copy(src1, dst1)

    add_post_without_text(os.path.join(target_dir, "posts"))

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
