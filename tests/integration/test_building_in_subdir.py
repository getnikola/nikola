"""
Check that running nikola from subdir works.

Check whether build works from posts/
"""

import os

import pytest

from nikola import __main__

from .helper import cd
from .test_demo_build import prepare_demo_site
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

    build_dir = os.path.join(target_dir, "posts")

    with cd(build_dir):
        __main__.main(["build"])
