"""Test if category destpath indexes avoid pages."""

import os

import pytest

import nikola.plugins.command.init
from nikola import __main__
from nikola.utils import makedirs

from .helper import append_config, cd, create_simple_post
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


def test_destpath_with_avoidance(build, output_dir):
    """Test destpath categories page generation and avoidance."""

    def _make_output_path(dir, name):
        """Make a file path to the output."""
        return os.path.join(dir, name + ".html")

    cat1 = os.path.join(output_dir, "posts", "cat1")
    cat2 = os.path.join(output_dir, "posts", "cat2")

    index1 = _make_output_path(cat1, "index")
    index2 = _make_output_path(cat2, "index")

    # Do all files exist?
    assert os.path.isfile(index1)
    assert os.path.isfile(index2)

    # Are their contents correct?
    with open(index1, "r", encoding="utf-8") as fh:
        page = fh.read()

    assert "Posts about cat1" in page
    assert "test-destpath-p1" in page
    assert "test-destpath-p2" in page
    assert "test-destpath-p3" not in page

    with open(index2, "r", encoding="utf-8") as fh:
        page = fh.read()

    assert "Posts about cat2" not in page
    assert "This is a post that conflicts with cat2." in page


@pytest.fixture(scope="module")
def build(target_dir):
    """
    Add subdirectories and create a post in category "cat1" and a page
    with the same URL as the category index (created via destpaths).
    """
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    posts = os.path.join(target_dir, "posts")
    cat1 = os.path.join(posts, "cat1")
    cat2 = os.path.join(posts, "cat2")

    makedirs(cat1)
    makedirs(cat2)

    create_simple_post(cat1, "p1.txt", "test-destpath-p1", "This is a post in cat1.")
    create_simple_post(cat1, "p2.txt", "test-destpath-p2", "This is a post in cat1.")
    create_simple_post(cat2, "p3.txt", "test-destpath-p3", "This is a post in cat2.")
    create_simple_post(posts, "cat2.txt", "cat2", "This is a post that conflicts with cat2.")

    append_config(
        target_dir,
        """
PRETTY_URLS = True
CATEGORY_ALLOW_HIERARCHIES = True
CATEGORY_DESTPATH_AS_DEFAULT = True
CATEGORY_DESTPATH_TRIM_PREFIX = True
CATEGORY_PAGES_FOLLOW_DESTPATH = True
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
