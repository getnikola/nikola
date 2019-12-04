"""Test if PAGE_INDEX works, with different PRETTY_URLS=False settings."""

import io
import os

import pytest

import nikola.plugins.command.init
from nikola import __main__
from nikola.utils import makedirs

from ..base import cd
from .helper import append_config
from .test_page_index_pretty_urls import check_build_output
from .test_empty_build import test_archive_exists  # NOQA
from .test_demo_build import (  # NOQA
    test_index_in_sitemap, test_avoid_double_slash_in_rss)


def test_page_index(build, output_dir):
    """Test PAGE_INDEX."""

    def output_path(dir, name):
        """Make a file path to the output."""
        return os.path.join(dir, name + '.html')

    check_build_output(output_dir, output_path)


@pytest.fixture(scope="module")
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    pages = os.path.join(target_dir, "pages")
    subdir1 = os.path.join(target_dir, "pages", "subdir1")
    subdir2 = os.path.join(target_dir, "pages", "subdir2")
    subdir3 = os.path.join(target_dir, "pages", "subdir3")

    makedirs(subdir1)
    makedirs(subdir2)
    makedirs(subdir3)

    with io.open(os.path.join(pages, 'page0.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 0\n.. slug: page0\n\nThis is page 0.\n")

    with io.open(os.path.join(subdir1, 'page1.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 1\n.. slug: page1\n\nThis is page 1.\n")
    with io.open(os.path.join(subdir1, 'page2.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 2\n.. slug: page2\n\nThis is page 2.\n")

    with io.open(os.path.join(subdir2, 'page3.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 3\n.. slug: page3\n\nThis is page 3.\n")
    with io.open(os.path.join(subdir2, 'foo.txt'), "w+", encoding="utf8") as outf:
        outf.write(
            ".. title: Not the page index\n.. slug: index\n\nThis is not the page index.\n")

    with io.open(os.path.join(subdir3, 'page4.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 4\n.. slug: page4\n\nThis is page 4.\n")
    with io.open(os.path.join(subdir3, 'bar.php'), "w+", encoding="utf8") as outf:
        outf.write(
            ".. title: Still not the page index\n.. slug: index\n\nThis is not the page index either.\n")

    append_config(target_dir, """
PAGE_INDEX = True
PRETTY_URLS = False
PAGES = PAGES + (('pages/*.php', 'pages', 'page.tmpl'),)
""")

    with cd(target_dir):
        __main__.main(["build"])
