"""Check that dropping pages to the root doesn't break links."""

import io
import os
import shutil

import lxml
import pytest

import nikola.plugins.command.init
from nikola import __main__

from ..base import cd


def test_relative_links(build, output_dir):
    """Check that the links in a page are correct"""
    test_path = os.path.join(output_dir, "about-nikola.html")

    flag = False
    with io.open(test_path, "rb") as inf:
        data = inf.read()
        for _, _, url, _ in lxml.html.iterlinks(data):
            # Just need to be sure this one is ok
            if url.endswith("css"):
                assert not url.startswith("..")
                flag = True

    # But I also need to be sure it is there!
    assert flag


def test_index_in_sitemap(build, output_dir):
    """Test that the correct path is in sitemap, and not the wrong one."""
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with io.open(sitemap_path, "r", encoding="utf8") as inf:
        sitemap_data = inf.read()

    assert '<loc>https://example.com/</loc>' not in sitemap_data
    assert '<loc>https://example.com/blog/index.html</loc>' in sitemap_data


def test_avoid_double_slash_in_rss(build, output_dir):
    rss_path = os.path.join(output_dir, "rss.xml")
    with io.open(rss_path, "r", encoding="utf8") as inf:
        rss_data = inf.read()

    assert 'https://example.com//' not in rss_data


def test_archive_exists(build, output_dir):
    """Ensure the build did something."""
    index_path = os.path.join(output_dir, "archive.html")
    assert os.path.isfile(index_path)


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
        outf.write(
            ".. title: foobar\n"
            ".. slug: foobar\n"
            ".. date: 2013-03-06 19:08:15\n"
        )

    # Configure our pages to reside in the root
    conf_path = os.path.join(target_dir, "conf.py")
    with io.open(conf_path, "r", encoding="utf-8") as inf:
        data = inf.read()

    data = data.replace('("pages/*.txt", "pages", "page.tmpl"),',
                        '("pages/*.txt", "", "page.tmpl"),')
    data = data.replace('("pages/*.rst", "pages", "page.tmpl"),',
                        '("pages/*.rst", "", "page.tmpl"),')
    data = data.replace('# INDEX_PATH = ""',
                        'INDEX_PATH = "blog"')
    data += "\nPRETTY_URLS = False\nSTRIP_INDEXES = False"

    with io.open(conf_path, "w+", encoding="utf8") as outf:
        outf.write(data)
        outf.flush()

    with cd(target_dir):
        __main__.main(["build"])
