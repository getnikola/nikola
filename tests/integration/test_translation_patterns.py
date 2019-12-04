"""Check that the path.lang.ext TRANSLATIONS_PATTERN works too"""

import io
import os
import shutil

import lxml.html
import pytest

import nikola.plugins.command.init
from nikola import __main__

from ..base import cd
from .helper import patch_config
from .test_empty_build import (  # NOQA
    test_archive_exists, test_avoid_double_slash_in_rss, test_check_files,
    test_check_links, test_index_in_sitemap)


def test_translated_titles(build, output_dir, other_locale):
    """Check that translated title is picked up."""
    en_file = os.path.join(output_dir, "pages", "1", "index.html")
    pl_file = os.path.join(output_dir, other_locale, "pages", "1", "index.html")

    # Files should be created
    assert os.path.isfile(en_file)
    assert os.path.isfile(pl_file)

    # And now let's check the titles
    with io.open(en_file, 'r', encoding='utf8') as inf:
        doc = lxml.html.parse(inf)
        assert doc.find('//title').text == 'Foo | Demo Site'

    with io.open(pl_file, 'r', encoding='utf8') as inf:
        doc = lxml.html.parse(inf)
        assert doc.find('//title').text == 'Bar | Demo Site'


@pytest.fixture(scope="module")
def build(target_dir, other_locale):
    """
    Build the site.

    Set the TRANSLATIONS_PATTERN to the old v6 default.
    """
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    src = os.path.join(os.path.dirname(__file__),
                       '..', 'data', 'translated_titles')
    for root, dirs, files in os.walk(src):
        for src_name in files:
            rel_dir = os.path.relpath(root, src)
            dst_file = os.path.join(target_dir, rel_dir, src_name)
            src_file = os.path.join(root, src_name)
            shutil.copy2(src_file, dst_file)

    os.rename(os.path.join(target_dir, "pages", "1.%s.txt" % other_locale),
              os.path.join(target_dir, "pages", "1.txt.%s" % other_locale))

    patch_config(target_dir, ('TRANSLATIONS_PATTERN = "{path}.{lang}.{ext}"',
                              'TRANSLATIONS_PATTERN = "{path}.{ext}.{lang}"'))

    with cd(target_dir):
        __main__.main(["build"])
