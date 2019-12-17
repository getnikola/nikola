"""Test if section indexes avoid pages."""

import io
import os

import pytest

import nikola.plugins.command.init
from nikola import __main__
from nikola.utils import makedirs

from .helper import append_config, cd
from .test_empty_build import (  # NOQA
    test_archive_exists, test_avoid_double_slash_in_rss, test_check_files,
    test_check_links, test_index_in_sitemap)


def test_section_index_avoidance(build, output_dir):
    """Test section index."""

    def _make_output_path(dir, name):
        """Make a file path to the output."""
        return os.path.join(dir, name + '.html')

    sec1 = os.path.join(output_dir, "sec1")
    colliding = os.path.join(output_dir, "sec1", "post0")

    # Do all files exist?
    assert os.path.isfile(_make_output_path(sec1, 'index'))
    assert os.path.isfile(_make_output_path(colliding, 'index'))

    # Is it really a page?
    with io.open(os.path.join(sec1, 'index.html'), 'r', encoding='utf-8') as fh:
        page = fh.read()

    assert 'This is Page 0' in page
    assert 'This is Post 0' not in page


@pytest.fixture(scope="module")
def build(target_dir):
    """
    Add subdirectories and create a post in section "sec1" and a page
    with the same URL as the section index.

    It also enables post sections.
    """
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    pages = os.path.join(target_dir, "pages")
    posts = os.path.join(target_dir, "posts")
    sec1 = os.path.join(posts, "sec1")

    makedirs(pages)
    makedirs(sec1)

    with io.open(os.path.join(pages, 'sec1.txt'), "w+", encoding="utf8") as outf:
        outf.write("""\
.. title: Page 0
.. slug: sec1

This is Page 0.
""")

    with io.open(os.path.join(sec1, 'colliding.txt'), "w+", encoding="utf8") as outf:
        outf.write("""\
.. title: Post 0
.. slug: post0
.. date: 2013-03-06 19:08:15

This is Post 0.
""")

    append_config(target_dir, """
POSTS_SECTIONS = True
POSTS_SECTIONS_ARE_INDEXES = True
PRETTY_URLS = True
POSTS = (('posts/*.txt', '', 'post.tmpl'),)
PAGES = (('pages/*.txt', '', 'page.tmpl'),)
""")

    with cd(target_dir):
        __main__.main(["build"])
