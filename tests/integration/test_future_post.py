"""Test a site with future posts."""

import os
from datetime import timedelta
from pathlib import Path
from textwrap import dedent

import pytest

import nikola
import nikola.plugins.command.init
from nikola.utils import current_time
from nikola import __main__

from .helper import append_config, cd
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


def test_future_post_deployment(build, output_dir, target_dir):
    """ Ensure that the future post is deleted upon deploying. """
    index_path = os.path.join(output_dir, "index.html")
    post_in_past = os.path.join(output_dir, "posts", "foo", "index.html")
    post_in_future = os.path.join(output_dir, "posts", "bar", "index.html")

    assert os.path.isfile(index_path)
    assert os.path.isfile(post_in_past)
    assert os.path.isfile(post_in_future)

    # Run deploy command to see if future post is deleted
    with cd(target_dir):
        __main__.main(["deploy"])

    assert os.path.isfile(index_path)
    assert os.path.isfile(post_in_past)
    assert not os.path.isfile(post_in_future)


@pytest.mark.parametrize("filename", ["index.html", "sitemap.xml"])
def test_future_post_not_in_indexes(build, output_dir, filename):
    """ Ensure that the future post is not present in the index and sitemap."""
    filepath = Path(output_dir) / filename
    assert filepath.is_file()

    content = filepath.read_text(encoding="utf8")

    assert "foo/" in content
    assert "bar/" not in content
    assert "baz" not in content


@pytest.fixture(scope="module")
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    # Change COMMENT_SYSTEM_ID to not wait for 5 seconds
    append_config(target_dir, '\nCOMMENT_SYSTEM_ID = "nikolatest"\n')

    def format_datetime(datetime):
        return datetime.strftime("%Y-%m-%d %H:%M:%S")

    past_datetime = format_datetime(current_time() + timedelta(days=-1))
    (Path(target_dir) / "posts" / "empty1.txt").write_text(
        dedent(f"""\
            .. title: foo
            .. slug: foo
            .. date: {past_datetime}
            """),
        encoding="utf8")

    future_datetime = format_datetime(current_time() + timedelta(days=1))

    (Path(target_dir) / "posts" / "empty2.txt").write_text(
        dedent(f"""\
            .. title: bar
            .. slug: bar
            .. date: {future_datetime}
            """),
        encoding="utf8")

    (Path(target_dir) / "posts" / "empty3.txt").write_text(
        dedent(f"""\
            .. title: baz
            .. slug: baz
            .. date: {future_datetime}
            .. pretty_url: false
            """),
        encoding="utf8")

    with cd(target_dir):
        __main__.main(["build"])
