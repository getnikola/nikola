"""Check external REDIRECTIONS"""

import os

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


def test_external_redirection(build, output_dir):
    ext_link = os.path.join(output_dir, 'external.html')

    assert os.path.exists(ext_link)
    with open(ext_link) as ext_link_fd:
        ext_link_content = ext_link_fd.read()

    redirect_tag = '<meta http-equiv="refresh" content="0; url=http://www.example.com/">'
    assert redirect_tag in ext_link_content


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    append_config(
        target_dir,
        """
REDIRECTIONS = [ ("external.html", "http://www.example.com/"), ]
""",
    )

    with cd(target_dir):
        __main__.main(["build"])
