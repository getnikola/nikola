"""
Check REDIRECTIONS.

This module tests absolute, external and relative redirects.
Each of the different redirect types is specified in the config and
then tested by at least one test."""

import io
import os

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
    abs_source = os.path.join(output_dir, "redirects", "absolute_source.html")
    assert os.path.exists(abs_source)

    abs_destination = os.path.join(output_dir, "posts", "absolute.html")
    assert os.path.exists(abs_destination)

    with open(abs_destination) as abs_destination_fd:
        abs_destination_content = abs_destination_fd.read()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=/redirects/absolute_source.html">'
    assert redirect_tag in abs_destination_content

    with open(abs_source) as abs_source_fd:
        absolute_source_content = abs_source_fd.read()

    assert absolute_source_content == "absolute"


def test_external_redirection(build, output_dir):
    ext_link = os.path.join(output_dir, "external.html")

    assert os.path.exists(ext_link)
    with open(ext_link) as ext_link_fd:
        ext_link_content = ext_link_fd.read()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=http://www.example.com/">'
    assert redirect_tag in ext_link_content


def test_relative_redirection(build, output_dir):
    rel_destination = os.path.join(output_dir, "relative.html")
    assert os.path.exists(rel_destination)
    rel_source = os.path.join(output_dir, "redirects", "rel_src.html")
    assert os.path.exists(rel_source)

    with open(rel_destination) as rel_destination_fd:
        rel_destination_content = rel_destination_fd.read()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=redirects/rel_src.html">'
    assert redirect_tag in rel_destination_content

    with open(rel_source) as rel_source_fd:
        rel_source_content = rel_source_fd.read()

    assert rel_source_content == "relative"


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    redirects_dir = os.path.join(target_dir, "files", "redirects")
    nikola.utils.makedirs(redirects_dir)

    # Source file for absolute redirect
    target_path = os.path.join(redirects_dir, "absolute_source.html")
    with io.open(target_path, "w+", encoding="utf8") as outf:
        outf.write("absolute")

    # Source file for relative redirect
    target_path = os.path.join(redirects_dir, "rel_src.html")
    with io.open(target_path, "w+", encoding="utf8") as outf:
        outf.write("relative")

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
