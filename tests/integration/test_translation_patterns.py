"""Check that the path.lang.ext TRANSLATIONS_PATTERN works too"""

import os
import shutil

import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import cd, patch_config
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)
from .test_translated_content import test_translated_titles  # NOQA


@pytest.fixture(scope="module")
def build(target_dir, test_dir, other_locale):
    """
    Build the site.

    Set the TRANSLATIONS_PATTERN to the old v6 default.
    """
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    src = os.path.join(test_dir, "..", "data", "translated_titles")
    for root, dirs, files in os.walk(src):
        for src_name in files:
            rel_dir = os.path.relpath(root, src)
            dst_file = os.path.join(target_dir, rel_dir, src_name)
            src_file = os.path.join(root, src_name)
            shutil.copy2(src_file, dst_file)

    os.rename(
        os.path.join(target_dir, "pages", "1.%s.txt" % other_locale),
        os.path.join(target_dir, "pages", "1.txt.%s" % other_locale),
    )

    patch_config(
        target_dir,
        (
            'TRANSLATIONS_PATTERN = "{path}.{lang}.{ext}"',
            'TRANSLATIONS_PATTERN = "{path}.{ext}.{lang}"',
        ),
    )

    with cd(target_dir):
        __main__.main(["build"])
