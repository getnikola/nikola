"""Check REDIRECTIONS"""

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


def test_absolute_redirection(build, output_dir):
    abs_source = os.path.join(output_dir, "redirects", "absolute_source.html")
    assert os.path.exists(abs_source)

    abs_destination = os.path.join(output_dir, "posts", "absolute.html")
    assert os.path.exists(abs_destination)

    with open(abs_destination) as abs_destination_fd:
        abs_destination_content = abs_destination_fd.read()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=/redirects/absolute_source.html">'
    assert redirect_tag in abs_destination_content

    with open(abs_source) as abs_source_fd:
        absolute_source_content = abs_source_fd.read()

    assert absolute_source_content == 'absolute'


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    redirects_dir = os.path.join(target_dir, "files", "redirects")
    nikola.utils.makedirs(redirects_dir)

    target_path = os.path.join(redirects_dir, "absolute_source.html")
    with io.open(target_path, "w+", encoding="utf8") as outf:
        outf.write("absolute")

    append_config(
        target_dir,
        """
REDIRECTIONS = [ ("posts/absolute.html", "/redirects/absolute_source.html"), ]
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
