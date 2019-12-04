"""Check external REDIRECTIONS"""

import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from ..base import cd
from .helper import add_post_without_text, append_config
from .test_empty_build import test_archive_exists  # NOQA
from .test_demo_build import (  # NOQA
    test_index_in_sitemap, test_avoid_double_slash_in_rss)
from .test_check import test_check_files, test_check_links  # NOQA


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.copy_sample_site(target_dir)
    init_command.create_configuration(target_dir)

    src1 = os.path.join(os.path.dirname(__file__),
                        '..', 'data', '1-nolinks.rst')
    dst1 = os.path.join(target_dir, 'posts', '1.rst')
    shutil.copy(src1, dst1)

    add_post_without_text(os.path.join(target_dir, 'posts'))

    append_config(target_dir, """
REDIRECTIONS = [ ("foo.html", "http://www.example.com/"), ]
""")

    with cd(target_dir):
        __main__.main(["build"])
