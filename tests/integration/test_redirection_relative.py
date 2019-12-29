"""Check relative REDIRECTIONS"""

import io
import os

import pytest

import nikola.plugins.command.init
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

    redirects_dir = os.path.join(target_dir, "files", "redirects")
    nikola.utils.makedirs(redirects_dir)

    target_path = os.path.join(redirects_dir, "rel_src.html")
    with io.open(target_path, "w+", encoding="utf8") as outf:
        outf.write("relative")

    append_config(
        target_dir,
        """
REDIRECTIONS = [ ("relative.html", "redirects/rel_src.html"), ]
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
