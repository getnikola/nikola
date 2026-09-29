"""
Test that SHOW_UNTRANSLATED_POSTS=False affects the post_list shortcode.

A site with translations en+pl, a post that only exists in pl, and a page
using the post-list shortcode: the untranslated post must not appear in
the default-language listing.
"""

import io
import os
import shutil

import lxml.html
import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import cd


@pytest.fixture(scope="module")
def build(target_dir, test_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    src = os.path.join(test_dir, "..", "data", "post_list_untranslated")
    for root, dirs, files in os.walk(src):
        for src_name in files:
            rel_dir = os.path.relpath(root, src)
            dst_file = os.path.join(target_dir, rel_dir, src_name)
            src_file = os.path.join(root, src_name)
            shutil.copy2(src_file, dst_file)

    with cd(target_dir):
        __main__.main(["build"])


def test_post_list_hides_untranslated_posts(build, output_dir):
    """Untranslated posts must not appear in a post-list on the default language."""
    listing = os.path.join(output_dir, "pages", "listing", "index.html")
    assert os.path.isfile(listing)

    with io.open(listing, "r", encoding="utf8") as inf:
        doc = lxml.html.parse(inf)
        links = doc.findall("//div[@class='post-list']//li/a")
        texts = [link.text for link in links]
        assert "Foo" in texts
        assert "Bar" not in texts
