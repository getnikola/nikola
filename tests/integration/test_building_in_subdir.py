"""
Check that running nikola from subdir works.

Check whether build works from posts/
"""

import io
import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import target_dir, output_dir, fixIssue438, localeborg_setup  # NOQA
from ..base import cd


def test_index_in_sitemap(build, output_dir):  # NOQA
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with io.open(sitemap_path, "r", encoding="utf8") as inf:
        sitemap_data = inf.read()

    assert '<loc>https://example.com/</loc>' in sitemap_data


def test_avoid_double_slash_in_rss(build, output_dir):  # NOQA
    rss_path = os.path.join(output_dir, "rss.xml")
    with io.open(rss_path, "r", encoding="utf8") as inf:
        rss_data = inf.read()

    assert 'https://example.com//' not in rss_data


def test_archive_exists(build, output_dir):  # NOQA
    """Ensure the build did something."""
    index_path = os.path.join(output_dir, "archive.html")
    assert os.path.isfile(index_path)


@pytest.fixture
def build(build_dir, target_dir):  # NOQA
    """Fill the site with demo content and build it."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.copy_sample_site(target_dir)
    init_command.create_configuration(target_dir)

    src1 = os.path.join(os.path.dirname(__file__),
                        '..', 'data', '1-nolinks.rst')
    dst1 = os.path.join(target_dir, 'posts', '1.rst')
    shutil.copy(src1, dst1)
    # File for Issue #374 (empty post text)
    with io.open(os.path.join(target_dir, 'posts', 'empty.txt'), "w+", encoding="utf8") as outf:
        outf.write(
            ".. title: foobar\n"
            ".. slug: foobar\n"
            ".. date: 2013-03-06 19:08:15\n"
        )

    with cd(build_dir):
        result = __main__.main(['build'])
        assert result == 0


@pytest.fixture
def build_dir(target_dir):  # NOQA
    return os.path.join(target_dir, 'posts')
