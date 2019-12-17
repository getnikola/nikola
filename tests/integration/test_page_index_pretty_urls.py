"""Test if PAGE_INDEX works, with different PRETTY_URLS=True."""

import os

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import append_config, cd
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)
from .test_page_index_normal_urls import create_pages
from .test_page_index_normal_urls import (  # NOQA
    test_page_index,
    test_page_index_in_subdir,
    test_page_index_content_in_pages,
    test_page_index_content_in_subdir1,
    test_page_index_content_in_subdir2,
    test_page_index_content_in_subdir3,
)


@pytest.fixture(scope="module")
def output_path_func():
    def output_path(dir, name):
        """Make a file path to the output."""
        return os.path.join(dir, name + "/index.html")

    return output_path


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
PRETTY_URLS = True
PAGES = PAGES + (('pages/*.php', 'pages', 'page.tmpl'),)
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
