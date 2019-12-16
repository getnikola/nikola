"""Check relative REDIRECTIONS"""

import io
import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from ..base import cd
from .helper import add_post_without_text, append_config
from .test_empty_build import (  # NOQA
    test_archive_exists, test_avoid_double_slash_in_rss, test_check_files,
    test_check_links, test_index_in_sitemap)


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

    add_post_without_text(os.path.join(target_dir, 'posts'))

    nikola.utils.makedirs(os.path.join(target_dir, "files", "foo"))

    target_path = os.path.join(target_dir, "files", "foo", "bar.html")
    with io.open(target_path, "w+", encoding="utf8") as outf:
        outf.write("foo")

    append_config(target_dir, """
REDIRECTIONS = [ ("foo.html", "foo/bar.html"), ]
""")

    with cd(target_dir):
        __main__.main(["build"])