"""
Test that a default build of a new site based on the demo site works.

This module also is one place where green path tests (working as
expected) for the `check` command are tested.
In this case these are tested against the demo site with default
settings.
"""

import datetime
import email
import itertools
import os
import time

import feedparser
import freezegun
import pytest

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

BUILDTIME = datetime.datetime(2023, 4, 5, 23, 59, 58, tzinfo=datetime.timezone.utc)


class Any:
    """Compare equal with anything. Use for expected values we don't care about."""
    def __eq__(self, _):
        return True


def rfc822(t):
    """Format a datetime according to RFC822, eg 'Wed, 05 Apr 2023 23:59:58 GMT'"""
    return email.utils.formatdate(
        time.mktime(BUILDTIME.astimezone().timetuple()),
        usegmt=True,
    )


def test_gallery_rss(build, output_dir):
    # Given a build of the demo samplesite in 'output_dir'
    # When we look for the RSS file of the "Demo" gallery
    rss_path = os.path.join(output_dir, 'galleries', 'demo', 'rss.xml')

    # Then it exists
    assert os.path.isfile(rss_path)
    # and it contains text
    with open(rss_path) as fp:
        content = fp.read()
    assert isinstance(content, str)
    assert len(content) > 0
    # and the text can be parsed as valid RSS
    parsed = feedparser.parse(content)
    # and the RSS contains top level attributes:
    assert parsed.version == 'rss20'
    # and the RSS contains feed attributes, about the gallery:
    assert parsed.feed.language == 'en'
    assert parsed.feed.link == 'https://example.com/galleries/demo/rss.xml'
    # TODO I think the following is a bug: The feed title should be the Gallery name,
    #      not the name of the gallery's final image.
    assert parsed.feed.title == 'Tesla tower1 lg'
    # TODO I think the following is a bug: The feed's subtitle (aka description) should
    #      contain the content of the gallery's index.txt.
    assert parsed.feed.subtitle == ''  # From the XML field 'description'
    assert parsed.feed.updated == rfc822(BUILDTIME)
    # and the images, as items in the RSS feed, are:
    expected_items = [
        dict(
            id='galleries/demo/tesla4_lg.jpg',
            link='https://example.com/galleries/demo/tesla4_lg.jpg',
            links=[
                Any(),
                dict(
                    href='https://example.com/galleries/demo/tesla4_lg.jpg',
                    length='30200',
                    rel='enclosure',
                    type='image/jpeg',
                ),
            ],
            published='Wed, 01 Jan 2014 00:01:00 GMT',
            title='Tesla4 lg',
        ),
        dict(
            id='galleries/demo/tesla_conducts_lg.webp',
            link='https://example.com/galleries/demo/tesla_conducts_lg.webp',
            links=[
                Any(),
                dict(
                    href='https://example.com/galleries/demo/tesla_conducts_lg.webp',
                    length='9620',
                    rel='enclosure',
                    type='image/webp',
                ),
            ],
            published='Wed, 01 Jan 2014 00:02:00 GMT',
            title='Tesla conducts lg',
        ),
        dict(
            id='galleries/demo/tesla_lightning1_lg.jpg',
            link='https://example.com/galleries/demo/tesla_lightning1_lg.jpg',
            links=[
                Any(),
                dict(
                    href='https://example.com/galleries/demo/tesla_lightning1_lg.jpg',
                    length='41123',
                    rel='enclosure',
                    type='image/jpeg',
                ),
            ],
            published='Wed, 01 Jan 2014 00:03:00 GMT',
            title='Tesla lightning1 lg',
        ),
        dict(
            id='galleries/demo/tesla_lightning2_lg.jpg',
            link='https://example.com/galleries/demo/tesla_lightning2_lg.jpg',
            links=[
                Any(),
                dict(
                    href='https://example.com/galleries/demo/tesla_lightning2_lg.jpg',
                    length='36994',
                    rel='enclosure',
                    type='image/jpeg',
                ),
            ],
            published='Wed, 01 Jan 2014 00:04:00 GMT',
            title='Tesla lightning2 lg',
        ),
        dict(
            id='galleries/demo/tesla_tower1_lg.jpg',
            link='https://example.com/galleries/demo/tesla_tower1_lg.jpg',
            links=[
                Any(),
                dict(
                    href='https://example.com/galleries/demo/tesla_tower1_lg.jpg',
                    length='18105',
                    rel='enclosure',
                    type='image/jpeg',
                )
            ],
            published='Wed, 01 Jan 2014 00:05:00 GMT',
            title='Tesla tower1 lg',
        ),
    ]
    for index, (actual, expected) in enumerate(
        itertools.zip_longest(parsed.entries, expected_items)
    ):
        for key, value in expected.items():
            assert actual[key] == value, f'item [{index}][{key!r}] {actual}'


@pytest.fixture(scope="module")
def build(target_dir):
    """Fill the site with demo content and build it."""
    prepare_demo_site(target_dir)

    with cd(target_dir):
        with freezegun.freeze_time(BUILDTIME):
            __main__.main(["build"])


def prepare_demo_site(target_dir):
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.copy_sample_site(target_dir)
    init_command.create_configuration(target_dir)

    posts_dir = os.path.join(target_dir, "posts")
    copy_example_post(posts_dir)
    add_post_without_text(posts_dir)
