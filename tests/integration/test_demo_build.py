"""
Test that a default build of a new site based on the demo site works.

This module also is one place where green path tests (working as
expected) for the `check` command are tested.
In this case these are tested against the demo site with default
settings.
"""

import os

import pytest
import rss_parser

import nikola.plugins.command.init
from nikola import __main__

from .helper import add_post_without_text, cd, copy_example_post
from .test_empty_build import (  # NOQA
    test_archive_exists,
    test_avoid_double_slash_in_rss,
    test_check_files,
    test_check_links,
    test_index_in_sitemap,
)


def to_dict(obj, *attrs):
    """Return a dict composed of the given attrs, taken from obj"""
    return {name: getattr(obj, name) for name in attrs}


def test_gallery_rss(build, output_dir):
    # Given a build of the demo samplesite in 'output_dir'
    # When we look for the RSS file of the "Demo" gallery
    # TODO Can I rely on the name of 'galleries' during tests,
    #      or should I be using/setting config->GALLERY_FOLDERS?
    rss_path = os.path.join(output_dir, 'galleries', 'demo', 'rss.xml')
    # Then it exists
    assert os.path.isfile(rss_path)
    # and it contains text
    with open(rss_path) as fp:
        content = fp.read()
    assert isinstance(content, str)
    assert len(content) > 0
    # and the text is valid RSS
    parsed = rss_parser.Parser(xml=content).parse()
    # and the RSS contains gallery attributes:
    # TODO Should the title be the name of the gallery, not the final image in it?
    assert parsed.title == 'Tesla conducts lg'
    assert parsed.version == '2.0'
    assert parsed.language == 'en'
    # TODO Should the gallery description contain the content of the index.txt file?
    assert parsed.description == ''
    # and the image items in the RSS feed are:
    expected_items = [
        dict(
            title='Tesla4 lg',
            link='https://example.com/galleries/demo/tesla4_lg.jpg',
            publish_date='Wed, 01 Jan 2014 00:01:00 GMT',
        ),
        dict(
            title='Tesla lightning1 lg',
            link='https://example.com/galleries/demo/tesla_lightning1_lg.jpg',
            publish_date='Wed, 01 Jan 2014 00:03:00 GMT',
        ),
        dict(
            title='Tesla lightning2 lg',
            link='https://example.com/galleries/demo/tesla_lightning2_lg.jpg',
            publish_date='Wed, 01 Jan 2014 00:04:00 GMT',
        ),
        dict(
            title='Tesla tower1 lg',
            link='https://example.com/galleries/demo/tesla_tower1_lg.jpg',
            publish_date='Wed, 01 Jan 2014 00:05:00 GMT',
        ),
        dict(
            title='Tesla conducts lg',
            link='https://example.com/galleries/demo/tesla_conducts_lg.webp',
            publish_date='Mon, 27 Mar 2023 18:18:55 GMT',
        ),
    ]
    for item, expected in zip(parsed.feed, expected_items):
        actual = to_dict(item, 'title', 'link', 'publish_date')
        assert actual == expected


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    with cd(target_dir):
        __main__.main(["build"])


def prepare_demo_site(target_dir):
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.copy_sample_site(target_dir)
    init_command.create_configuration(target_dir)

    posts_dir = os.path.join(target_dir, "posts")
    copy_example_post(posts_dir)
    add_post_without_text(posts_dir)
