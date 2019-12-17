"""The demo build should pass 'nikola check' and fail with missing files."""

import io
import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import add_post_without_text, cd
from .test_empty_build import (  # NOQA
    test_avoid_double_slash_in_rss,
    test_index_in_sitemap,
)


def test_check_links_fail(build, output_dir, target_dir):
    os.unlink(os.path.join(output_dir, "archive.html"))

    with cd(target_dir):
        result = __main__.main(["check", "-l"])
        assert result != 0


def test_check_files_fail(build, output_dir, target_dir):
    manually_added_file = os.path.join(output_dir, "foobar")
    with io.open(manually_added_file, "w+", encoding="utf8") as outf:
        outf.write("foo")

    with cd(target_dir):
        result = __main__.main(["check", "-f"])
        assert result != 0


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

    with cd(target_dir):
        __main__.main(["build"])
