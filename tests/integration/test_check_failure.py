"""The demo build should pass 'nikola check' and fail with missing files."""

import io
import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from ..base import cd


def test_check_links_fail(build, output_dir, target_dir):
    os.unlink(os.path.join(output_dir, "archive.html"))

    with cd(target_dir):
        result = __main__.main(['check', '-l'])
        assert result != 0


def test_check_files_fail(build, output_dir, target_dir):
    manually_added_file = os.path.join(output_dir, "foobar")
    with io.open(manually_added_file, "w+", encoding="utf8") as outf:
        outf.write("foo")

    with cd(target_dir):
        result = __main__.main(['check', '-f'])
        assert result != 0


def test_index_in_sitemap(build, output_dir):
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with io.open(sitemap_path, "r", encoding="utf8") as inf:
        sitemap_data = inf.read()

    assert '<loc>https://example.com/</loc>' in sitemap_data


def test_avoid_double_slash_in_rss(build, output_dir):
    rss_path = os.path.join(output_dir, "rss.xml")
    with io.open(rss_path, "r", encoding="utf8") as inf:
        rss_data = inf.read()

    assert 'https://example.com//' not in rss_data


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
    # File for Issue #374 (empty post text)
    with io.open(os.path.join(target_dir, 'posts', 'empty.txt'), "w+", encoding="utf8") as outf:
        outf.write("""\
.. title: foobar
.. slug: foobar
.. date: 2013-03-06 19:08:15
""")

    with cd(target_dir):
        __main__.main(["build"])
