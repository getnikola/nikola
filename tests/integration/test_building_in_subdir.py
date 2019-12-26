"""
Check that running nikola from subdir works.

Check whether build works from posts/
"""

import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import add_post_without_text, cd
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


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

    build_dir = os.path.join(target_dir, "posts")

    with cd(build_dir):
        result = __main__.main(["build"])
        assert result == 0
