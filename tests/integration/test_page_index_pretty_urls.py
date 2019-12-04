"""Test if PAGE_INDEX works, with different PRETTY_URLS=True."""

import io
import os

import pytest

import nikola.plugins.command.init
from nikola import __main__
from nikola.utils import makedirs

from ..base import cd
from .helper import append_config
from .test_empty_build import test_archive_exists  # NOQA
from .test_demo_build import test_index_in_sitemap  # NOQA


def test_page_index(build, output_dir):
    """Test PAGE_INDEX."""

    def output_path(dir, name):
        """Make a file path to the output."""
        return os.path.join(dir, name + '/index.html')

    check_build_output(output_dir, output_path)


def check_build_output(output_dir, path_func):
    pages = os.path.join(output_dir, "pages")
    subdir1 = os.path.join(output_dir, "pages", "subdir1")
    subdir2 = os.path.join(output_dir, "pages", "subdir2")
    subdir3 = os.path.join(output_dir, "pages", "subdir3")

    # Do all files exist?
    assert os.path.isfile(path_func(pages, 'page0'))
    assert os.path.isfile(path_func(subdir1, 'page1'))
    assert os.path.isfile(path_func(subdir1, 'page2'))
    assert os.path.isfile(path_func(subdir2, 'page3'))
    assert os.path.isfile(path_func(subdir3, 'page4'))

    assert os.path.isfile(os.path.join(pages, 'index.html'))
    assert os.path.isfile(os.path.join(subdir1, 'index.html'))
    assert os.path.isfile(os.path.join(subdir2, 'index.html'))
    assert os.path.isfile(os.path.join(subdir3, 'index.php'))
    assert not os.path.isfile(os.path.join(subdir3, 'index.html'))

    # Do the indexes only contain the pages the should?
    with io.open(os.path.join(pages, 'index.html'), 'r', encoding='utf-8') as fh:
        pages_index = fh.read()
    assert 'Page 0' in pages_index
    assert 'Page 1' not in pages_index
    assert 'Page 2' not in pages_index
    assert 'Page 3' not in pages_index
    assert 'Page 4' not in pages_index
    assert 'This is not the page index' not in pages_index

    with io.open(os.path.join(subdir1, 'index.html'), 'r', encoding='utf-8') as fh:
        subdir1_index = fh.read()
    assert 'Page 0' not in subdir1_index
    assert 'Page 1' in subdir1_index
    assert 'Page 2' in subdir1_index
    assert 'Page 3' not in subdir1_index
    assert 'Page 4' not in subdir1_index
    assert 'This is not the page index' not in subdir1_index

    with io.open(os.path.join(subdir2, 'index.html'), 'r', encoding='utf-8') as fh:
        subdir2_index = fh.read()
    assert 'Page 0' not in subdir2_index
    assert 'Page 1' not in subdir2_index
    assert 'Page 2' not in subdir2_index
    assert 'Page 3' not in subdir2_index
    assert 'Page 4' not in subdir2_index
    assert 'This is not the page index.' in subdir2_index

    with io.open(os.path.join(subdir3, 'index.php'), 'r', encoding='utf-8') as fh:
        subdir3_index = fh.read()
    assert 'Page 0' not in subdir3_index
    assert 'Page 1' not in subdir3_index
    assert 'Page 2' not in subdir3_index
    assert 'Page 3' not in subdir3_index
    assert 'Page 4' not in subdir3_index
    assert 'This is not the page index either.' in subdir3_index


@pytest.fixture(scope="module")
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    pages = os.path.join(target_dir, "pages")
    subdir1 = os.path.join(target_dir, "pages", "subdir1")
    subdir2 = os.path.join(target_dir, "pages", "subdir2")
    subdir3 = os.path.join(target_dir, "pages", "subdir3")

    makedirs(subdir1)
    makedirs(subdir2)
    makedirs(subdir3)

    with io.open(os.path.join(pages, 'page0.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 0\n.. slug: page0\n\nThis is page 0.\n")

    with io.open(os.path.join(subdir1, 'page1.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 1\n.. slug: page1\n\nThis is page 1.\n")
    with io.open(os.path.join(subdir1, 'page2.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 2\n.. slug: page2\n\nThis is page 2.\n")

    with io.open(os.path.join(subdir2, 'page3.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 3\n.. slug: page3\n\nThis is page 3.\n")
    with io.open(os.path.join(subdir2, 'foo.txt'), "w+", encoding="utf8") as outf:
        outf.write(
            ".. title: Not the page index\n.. slug: index\n\nThis is not the page index.\n")

    with io.open(os.path.join(subdir3, 'page4.txt'), "w+", encoding="utf8") as outf:
        outf.write(".. title: Page 4\n.. slug: page4\n\nThis is page 4.\n")
    with io.open(os.path.join(subdir3, 'bar.php'), "w+", encoding="utf8") as outf:
        outf.write(
            ".. title: Still not the page index\n.. slug: index\n\nThis is not the page index either.\n")

    append_config(target_dir, """
PAGE_INDEX = True
PRETTY_URLS = True
PAGES = PAGES + (('pages/*.php', 'pages', 'page.tmpl'),)
""")

    with cd(target_dir):
        __main__.main(["build"])
