"""Test a site with future posts."""

import io
import os
from datetime import timedelta

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
    filepath = os.path.join(output_dir, filename)
    assert os.path.isfile(filepath)

    with io.open(filepath, "r", encoding="utf8") as inf:
        content = inf.read()
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
    with io.open(
        os.path.join(target_dir, "posts", "empty1.txt"), "w+", encoding="utf8"
    ) as past_post:
        past_post.write(
            """\
.. title: foo
.. slug: foo
.. date: %s
"""
            % past_datetime
        )

    future_datetime = format_datetime(current_time() + timedelta(days=1))
    with io.open(
        os.path.join(target_dir, "posts", "empty2.txt"), "w+", encoding="utf8"
    ) as future_post:
        future_post.write(
            """\
.. title: bar
.. slug: bar
.. date: %s
"""
            % future_datetime
        )

    with io.open(
        os.path.join(target_dir, "posts", "empty3.txt"), "w+", encoding="utf8"
    ) as future_post:
        future_post.write(
            """\
.. title: baz
.. slug: baz
.. date: %s
.. pretty_url: false
"""
            % future_datetime
        )

    with cd(target_dir):
        __main__.main(["build"])
