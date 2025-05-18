"""
Check REDIRECTIONS.

This module tests absolute, external and relative redirects.
Each of the different redirect types is specified in the config and
then tested by at least one test."""

import os
from pathlib import Path

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import append_config, cd
from .test_demo_build import prepare_demo_site
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


def test_absolute_redirection(build, output_dir):
    abs_source = Path(output_dir) / "redirects" / "absolute_source.html"
    assert abs_source.exists()

    abs_destination = Path(output_dir) / "posts" / "absolute.html"
    assert abs_destination.exists()

    abs_destination_content = abs_destination.read_text()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=/redirects/absolute_source.html">'
    assert redirect_tag in abs_destination_content

    absolute_source_content = abs_source.read_text()

    assert absolute_source_content == "absolute"


def test_external_redirection(build, output_dir):
    ext_link = Path(output_dir) / "external.html"

    assert ext_link.exists()

    ext_link_content = ext_link.read_text()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=http://www.example.com/">'
    assert redirect_tag in ext_link_content


def test_relative_redirection(build, output_dir):
    rel_destination = Path(output_dir) / "relative.html"
    assert rel_destination.exists()

    rel_source = Path(output_dir) / "redirects" / "rel_src.html"
    assert rel_source.exists()

    rel_destination_content = rel_destination.read_text()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=redirects/rel_src.html">'
    assert redirect_tag in rel_destination_content

    rel_source_content = rel_source.read_text()

    assert rel_source_content == "relative"


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    redirects_dir = os.path.join(target_dir, "files", "redirects")
    nikola.utils.makedirs(redirects_dir)

    # Source file for absolute redirect
    target_path = Path(redirects_dir) / "absolute_source.html"
    target_path.write_text("absolute", encoding="utf8")

    # Source file for relative redirect
    target_path = Path(redirects_dir) / "rel_src.html"
    target_path.write_text("relative", encoding="utf8")

    # Configure usage of specific redirects
    append_config(
        target_dir,
        """
REDIRECTIONS = [
    ("posts/absolute.html", "/redirects/absolute_source.html"),
    ("external.html", "http://www.example.com/"),
    ("relative.html", "redirects/rel_src.html"),
]
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
