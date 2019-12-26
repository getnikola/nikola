"""
Duplicate POSTS in settings.

Should not read each post twice, which causes conflicts.
"""

import pytest

from nikola import __main__

from .helper import append_config, cd
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

    append_config(
        target_dir,
        """
POSTS = (("posts/*.txt", "posts", "post.tmpl"),
         ("posts/*.txt", "posts", "post.tmpl"))
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
