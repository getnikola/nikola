"""Check that the monthly archives build and are correct."""

import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from ..base import cd
from .helper import add_post_without_text, patch_config
from .test_empty_build import test_archive_exists  # NOQA
from .test_demo_build import (  # NOQA
    test_index_in_sitemap, test_avoid_double_slash_in_rss)


def test_monthly_archive(build, output_dir):
    """Check that the monthly archive is build."""
    assert os.path.isfile(os.path.join(output_dir, '2012', '03', 'index.html'))


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

    patch_config(target_dir, ('# CREATE_MONTHLY_ARCHIVE = False',
                              'CREATE_MONTHLY_ARCHIVE = True'))

    with cd(target_dir):
        __main__.main(["build"])
