"""Check that full archives build and are correct."""

import io
import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from ..base import cd


@pytest.mark.parametrize("path", [
    ['archive.html'],
    ['2012', 'index.html'],
    ['2012', '03', 'index.html'],
    ['2012', '03', '30', 'index.html'],
], ids=["overall", "year", "month", "day"])
def test_full_archive(build, output_dir, path):
    """Check existance of archive pages"""
    expected_path = os.path.join(output_dir, *path)
    assert os.path.isfile(expected_path)


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
    with io.open(os.path.join(target_dir, 'posts', 'empty.txt'), "w", encoding="utf8") as outf:
        outf.write("""\
.. title: foobar
.. slug: foobar
.. date: 2013-03-06 19:08:15
""")

    conf_path = os.path.join(target_dir, "conf.py")
    with io.open(conf_path, "r", encoding="utf-8") as inf:
        data = inf.read()

    data = data.replace('# CREATE_FULL_ARCHIVES = False',
                        'CREATE_FULL_ARCHIVES = True')

    with io.open(conf_path, "w+", encoding="utf8") as outf:
        outf.write(data)
        outf.flush()

    with cd(target_dir):
        __main__.main(["build"])
