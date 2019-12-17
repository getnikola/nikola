"""Performaning the build of an empty site."""

import io
import os

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import cd


def test_check_links(build, target_dir):
    with cd(target_dir):
        assert __main__.main(["check", "-l"]) is None


def test_check_files(build, target_dir):
    with cd(target_dir):
        assert __main__.main(["check", "-f"]) is None


def test_index_in_sitemap(build, output_dir):
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with io.open(sitemap_path, "r", encoding="utf8") as inf:
        sitemap_data = inf.read()

    assert "<loc>https://example.com/</loc>" in sitemap_data


def test_avoid_double_slash_in_rss(build, output_dir):
    rss_path = os.path.join(output_dir, "rss.xml")
    with io.open(rss_path, "r", encoding="utf8") as inf:
        rss_data = inf.read()

    assert "https://example.com//" not in rss_data


def test_archive_exists(build, output_dir):
    """Ensure the build did something."""
    index_path = os.path.join(output_dir, "archive.html")
    assert os.path.isfile(index_path)


@pytest.fixture(scope="module")
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    with cd(target_dir):
        __main__.main(["build"])
