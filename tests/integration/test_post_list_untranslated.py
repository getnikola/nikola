"""
Test that SHOW_UNTRANSLATED_POSTS=False affects the post_list shortcode.

A site with translations en+pl, a post that only exists in pl, and a page
using the post-list shortcode: the untranslated post must not appear in
the default-language listing.
"""

import io
import os

import lxml.html
import pytest

import nikola.plugins.command.init
from nikola import __main__

from .helper import append_config, cd, create_simple_post


@pytest.fixture(scope="module")
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    append_config(target_dir, """
TRANSLATIONS = {
    DEFAULT_LANG: "",
    "pl": "./pl",
}
SHOW_UNTRANSLATED_POSTS = False
""")

    create_simple_post(os.path.join(target_dir, "posts"), "foo.txt", "Foo")
    create_simple_post(os.path.join(target_dir, "posts"), "bar.pl.txt", "Bar")
    create_simple_post(
        os.path.join(target_dir, "pages"), "listing.txt", "listing", text="{{% post-list %}}"
    )

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
