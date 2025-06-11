"""
The demo build should pass 'nikola check' and fail with missing files.

This tests the red path (failures) for the `check` command.
Green path tests (working as expected) can be found in `test_demo_build`.
"""

import os
from pathlib import Path

import pytest

from nikola import __main__

from .helper import cd
from .test_demo_build import prepare_demo_site
from .test_empty_build import (  # NOQA
    test_avoid_double_slash_in_rss,
    test_index_in_sitemap,
)


def test_check_links_fail(build, output_dir, target_dir):
    os.unlink(Path(output_dir) / "archive.html")

    with cd(target_dir):
        result = __main__.main(["check", "-l"])
        assert result != 0


def test_check_files_fail(build, output_dir, target_dir):
    manually_added_file = Path(output_dir) / "foobar"
    manually_added_file.write_text("foo", encoding="utf8")

    with cd(target_dir):
        result = __main__.main(["check", "-f"])
        assert result != 0


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    with cd(target_dir):
        __main__.main(["build"])
