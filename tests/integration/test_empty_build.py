"""Performaning the build of an empty site."""

from pathlib import Path

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
    sitemap_path = Path(output_dir) / "sitemap.xml"
    sitemap_data = sitemap_path.read_text(encoding="utf8")

    assert "<loc>https://example.com/</loc>" in sitemap_data


def test_avoid_double_slash_in_rss(build, output_dir):
    rss_path = Path(output_dir) / "rss.xml"
    rss_data = rss_path.read_text(encoding="utf8")

    assert "https://example.com//" not in rss_data


def test_archive_exists(build, output_dir):
    """Ensure the build did something."""
    index_path = Path(output_dir) / "archive.html"
    assert index_path.is_file()


@pytest.fixture(scope="module")
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    with cd(target_dir):
        __main__.main(["build"])
