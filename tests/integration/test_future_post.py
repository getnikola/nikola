"""Test a site with future posts."""

import datetime
import io
import os
import sys

import pytest

import nikola
import nikola.plugins.command.init
from nikola.utils import LocaleBorg, current_time
from nikola import __main__

from ..base import cd

LOCALE_DEFAULT = os.environ.get('NIKOLA_LOCALE_DEFAULT', 'en')


def test_future_post(build, output_dir, target_dir):
    """ Ensure that the future post is not present in the index and sitemap."""
    index_path = os.path.join(output_dir, "index.html")
    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    foo_path = os.path.join(output_dir, "posts", "foo", "index.html")
    bar_path = os.path.join(output_dir, "posts", "bar", "index.html")
    assert os.path.isfile(index_path)
    assert os.path.isfile(sitemap_path)
    assert os.path.isfile(foo_path)
    assert os.path.isfile(bar_path)

    with io.open(index_path, "r", encoding="utf8") as inf:
        index_data = inf.read()
    assert 'foo/' in index_data
    assert 'bar/' not in index_data

    with io.open(sitemap_path, "r", encoding="utf8") as inf:
        sitemap_data = inf.read()
    assert 'foo/' in sitemap_data
    assert 'bar/' not in sitemap_data

    # Run deploy command to see if future post is deleted
    with cd(target_dir):
        __main__.main(["deploy"])

    assert os.path.isfile(index_path)
    assert os.path.isfile(foo_path)
    assert not os.path.isfile(bar_path)


def test_archive_exists(build, output_dir):
    """Ensure the build did something."""
    index_path = os.path.join(output_dir, "archive.html")
    assert os.path.isfile(index_path)


@pytest.fixture
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    # Change COMMENT_SYSTEM_ID to not wait for 5 seconds
    with io.open(os.path.join(target_dir, 'conf.py'), "a+", encoding="utf8") as config_file:
        config_file.write('\nCOMMENT_SYSTEM_ID = "nikolatest"\n')

    with io.open(os.path.join(target_dir, 'posts', 'empty1.txt'), "w+", encoding="utf8") as past_post:
        past_post.write(".. title: foo\n" ".. slug: foo\n" ".. date: %s\n" % (
            current_time() + datetime.timedelta(-1)).strftime('%Y-%m-%d %H:%M:%S'))

    with io.open(os.path.join(target_dir, 'posts', 'empty2.txt'), "w+", encoding="utf8") as future_post:
        future_post.write(".. title: bar\n" ".. slug: bar\n" ".. date: %s\n" % (
            current_time() + datetime.timedelta(1)).strftime('%Y-%m-%d %H:%M:%S'))

    with cd(target_dir):
        __main__.main(["build"])


@pytest.fixture
def output_dir(target_dir):
    return os.path.join(target_dir, "output")


@pytest.fixture
def target_dir(tmpdir):
    tdir = os.path.join(str(tmpdir), 'target')
    os.mkdir(tdir)
    yield tdir


@pytest.fixture(autouse=True)
def fixIssue438():
    try:
        yield
    finally:
        try:
            del sys.modules['conf']
        except KeyError:
            pass


@pytest.fixture(autouse=True)
def localeborg_setup():
    """
    Reset the LocaleBorg before and after every test.
    """
    LocaleBorg.reset()
    LocaleBorg.initialize({}, LOCALE_DEFAULT)
    try:
        yield
    finally:
        LocaleBorg.reset()
