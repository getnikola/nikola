"""Tests for the post-list shortcode."""

import pytest

from nikola.plugins.shortcode.post_list import PostListShortcode


class FakePost:
    """A post with just the attributes needed by the post-list shortcode."""

    def __init__(self, slug, is_post, use_in_feeds):
        self.slug = slug
        self.is_post = is_post
        self.use_in_feeds = use_in_feeds
        self.source_path = slug

    def translated_base_path(self, lang):
        return self.source_path


class FakeSite:
    """A site with just the attributes needed by the post-list shortcode."""

    invariant = True
    post_per_input_file = {}
    GLOBAL_CONTEXT = {'date_format': {'en': ''}}
    MESSAGES = {}

    def __init__(self, timeline):
        self.timeline = timeline
        self.template_system = self
        self.rendered_context = None

    def template_deps(self, template, context):
        return []

    def render_template(self, template, output_name, context):
        self.rendered_context = context
        return ''

    def link(self, *args, **kwargs):
        return ''


@pytest.mark.parametrize(
    ('post_type', 'expected_slugs'),
    [
        ('post', ['published-post', 'draft-post']),
        ('page', ['page']),
    ],
)
def test_post_list_filters_by_post_type_not_feed_membership(post_type, expected_slugs):
    """Draft posts remain posts even though they are excluded from feeds."""
    site = FakeSite(
        [
            FakePost('published-post', is_post=True, use_in_feeds=True),
            FakePost('draft-post', is_post=True, use_in_feeds=False),
            FakePost('page', is_post=False, use_in_feeds=False),
        ]
    )

    PostListShortcode().handler(site=site, lang='en', post_type=post_type)

    assert [post.slug for post in site.rendered_context['posts']] == expected_slugs
