"""
Test that a default build of a new site based on the demo site works.

This module also is one place where green path tests (working as
expected) for the `check` command are tested.
In this case these are tested against the demo site with default
settings.
"""

import os

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import add_post_without_text, cd, copy_example_post
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    with cd(target_dir):
        __main__.main(["build"])


def prepare_demo_site(target_dir):
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.copy_sample_site(target_dir)
    init_command.create_configuration(target_dir)

    posts_dir = os.path.join(target_dir, "posts")
    copy_example_post(posts_dir)
    add_post_without_text(posts_dir)
