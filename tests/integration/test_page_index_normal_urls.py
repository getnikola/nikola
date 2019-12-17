"""Test if PAGE_INDEX works, with different PRETTY_URLS=False settings."""

import io
import os

import pytest

import nikola.plugins.command.init
from nikola import __main__
from nikola.utils import makedirs

from .helper import append_config, cd
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


def get_last_folder_as_id(value):
    """Use the last part of the directories as test identifier."""
    if isinstance(value, (tuple,)):
        return value[-1]

    return value


@pytest.mark.parametrize(
    "dirs, expected_file",
    [
        (("pages",), "page0"),
        (("pages", "subdir1"), "page1"),
        (("pages", "subdir1"), "page2"),
        (("pages", "subdir2"), "page3"),
        (("pages", "subdir3"), "page4"),
    ],
    ids=get_last_folder_as_id,
)
def test_page_index(build, output_dir, dirs, expected_file, output_path_func):
    """Test PAGE_INDEX - Do all files exist?"""
    path_func = output_path_func

    checkdir = os.path.join(output_dir, *dirs)

    assert os.path.isfile(path_func(checkdir, expected_file))


@pytest.mark.parametrize(
    "dirs, expected_index_file",
    [
        (("pages",), "index.html"),
        (("pages", "subdir1"), "index.html"),
        (("pages", "subdir2"), "index.html"),
        (("pages", "subdir3"), "index.php"),
    ],
    ids=get_last_folder_as_id,
)
def test_page_index_in_subdir(build, output_dir, dirs, expected_index_file):
    """Test PAGE_INDEX - Do index files in subdir exist?"""
    checkdir = os.path.join(output_dir, *dirs)

    assert os.path.isfile(os.path.join(checkdir, expected_index_file))
    if expected_index_file == "index.php":
        assert not os.path.isfile(os.path.join(checkdir, "index.html"))


@pytest.fixture(scope="module")
def output_path_func():
    def output_path(dir, name):
        """Make a file path to the output."""
        return os.path.join(dir, name + ".html")

    return output_path


def test_page_index_content_in_pages(build, output_dir):
    """Do the indexes only contain the pages the should?"""
    pages = os.path.join(output_dir, "pages")

    with io.open(os.path.join(pages, "index.html"), "r", encoding="utf-8") as fh:
        pages_index = fh.read()

    assert "Page 0" in pages_index
    assert "Page 1" not in pages_index
    assert "Page 2" not in pages_index
    assert "Page 3" not in pages_index
    assert "Page 4" not in pages_index
    assert "This is not the page index" not in pages_index


def test_page_index_content_in_subdir1(build, output_dir):
    """Do the indexes only contain the pages the should?"""
    subdir1 = os.path.join(output_dir, "pages", "subdir1")

    with io.open(os.path.join(subdir1, "index.html"), "r", encoding="utf-8") as fh:
        subdir1_index = fh.read()

    assert "Page 0" not in subdir1_index
    assert "Page 1" in subdir1_index
    assert "Page 2" in subdir1_index
    assert "Page 3" not in subdir1_index
    assert "Page 4" not in subdir1_index
    assert "This is not the page index" not in subdir1_index


def test_page_index_content_in_subdir2(build, output_dir):
    """Do the indexes only contain the pages the should?"""
    subdir2 = os.path.join(output_dir, "pages", "subdir2")

    with io.open(os.path.join(subdir2, "index.html"), "r", encoding="utf-8") as fh:
        subdir2_index = fh.read()

    assert "Page 0" not in subdir2_index
    assert "Page 1" not in subdir2_index
    assert "Page 2" not in subdir2_index
    assert "Page 3" not in subdir2_index
    assert "Page 4" not in subdir2_index
    assert "This is not the page index." in subdir2_index


def test_page_index_content_in_subdir3(build, output_dir):
    """Do the indexes only contain the pages the should?"""
    subdir3 = os.path.join(output_dir, "pages", "subdir3")

    with io.open(os.path.join(subdir3, "index.php"), "r", encoding="utf-8") as fh:
        subdir3_index = fh.read()

    assert "Page 0" not in subdir3_index
    assert "Page 1" not in subdir3_index
    assert "Page 2" not in subdir3_index
    assert "Page 3" not in subdir3_index
    assert "Page 4" not in subdir3_index
    assert "This is not the page index either." in subdir3_index


@pytest.fixture(scope="module")
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    create_pages(target_dir)

    append_config(
        target_dir,
        """
PAGE_INDEX = True
PRETTY_URLS = False
PAGES = PAGES + (('pages/*.php', 'pages', 'page.tmpl'),)
""",
    )

    with cd(target_dir):
        __main__.main(["build"])


def create_pages(target_dir):
    pages = os.path.join(target_dir, "pages")
    subdir1 = os.path.join(target_dir, "pages", "subdir1")
    subdir2 = os.path.join(target_dir, "pages", "subdir2")
    subdir3 = os.path.join(target_dir, "pages", "subdir3")

    makedirs(subdir1)
    makedirs(subdir2)
    makedirs(subdir3)

    with io.open(os.path.join(pages, "page0.txt"), "w+", encoding="utf8") as outf:
        outf.write(
            """\
.. title: Page 0
.. slug: page0

This is page 0.
"""
        )

    with io.open(os.path.join(subdir1, "page1.txt"), "w+", encoding="utf8") as outf:
        outf.write(
            """\
.. title: Page 1
.. slug: page1

This is page 1.
"""
        )

    with io.open(os.path.join(subdir1, "page2.txt"), "w+", encoding="utf8") as outf:
        outf.write(
            """\
.. title: Page 2
.. slug: page2

This is page 2.
"""
        )

    with io.open(os.path.join(subdir2, "page3.txt"), "w+", encoding="utf8") as outf:
        outf.write(
            """\
.. title: Page 3
.. slug: page3

This is page 3.
"""
        )

    with io.open(os.path.join(subdir2, "foo.txt"), "w+", encoding="utf8") as outf:
        outf.write(
            """\
.. title: Not the page index
.. slug: index

This is not the page index.
"""
        )

    with io.open(os.path.join(subdir3, "page4.txt"), "w+", encoding="utf8") as outf:
        outf.write(
            """\
.. title: Page 4
.. slug: page4

This is page 4.
"""
        )

    with io.open(os.path.join(subdir3, "bar.php"), "w+", encoding="utf8") as outf:
        outf.write(
            """\
.. title: Still not the page index
.. slug: index

This is not the page index either.
"""
        )
