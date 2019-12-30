"""Make sure posts only in secondary languages work."""

import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import cd
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


@pytest.fixture(scope="module")
def build(target_dir, test_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    src = os.path.join(test_dir, "..", "data", "translated_titles")
    for root, dirs, files in os.walk(src):
        for src_name in files:
            if src_name == "1.txt":  # English post
                continue

            rel_dir = os.path.relpath(root, src)
            dst_file = os.path.join(target_dir, rel_dir, src_name)
            src_file = os.path.join(root, src_name)
            shutil.copy2(src_file, dst_file)

    with cd(target_dir):
        __main__.main(["build"])
