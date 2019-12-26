"""
Validate links in a site which is:

* built in URL_TYPE="full_path"
* deployable to a subfolder (BASE_URL="https://example.com/foo/")
"""

import pytest

from nikola import __main__

from .helper import cd, patch_config
from .test_check_absolute_subfolder import test_index_in_sitemap  # NOQA
from .test_demo_build import prepare_demo_site
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
)


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    patch_config(
        target_dir,
        ('SITE_URL = "https://example.com/"', 'SITE_URL = "https://example.com/foo/"'),
        ("# URL_TYPE = 'rel_path'", "URL_TYPE = 'full_path'"),
    )

    with cd(target_dir):
        __main__.main(["build"])
