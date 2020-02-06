import os
import re
from collections import defaultdict
from io import StringIO
from unittest import mock

import dateutil.tz
import pytest
from lxml import etree

from nikola.nikola import Nikola, Post
from nikola.utils import LocaleBorg, TranslatableSetting


def test_feed_is_valid(rss_feed_content, rss_schema):
    """
    A testcase to check if the generated feed is valid.

    Validation can be tested with W3 FEED Validator that can be found
    at http://feedvalidator.org
    """
    document = etree.parse(StringIO(rss_feed_content))

    assert rss_schema.validate(document)


@pytest.fixture
def rss_schema(rss_schema_filename):
    with open(rss_schema_filename, "r") as rss_schema_file:
        xmlschema_doc = etree.parse(rss_schema_file)

    return etree.XMLSchema(xmlschema_doc)


@pytest.fixture
def rss_schema_filename(test_dir):
    return os.path.join(test_dir, "data", "rss-2_0.xsd")


@pytest.mark.parametrize("element", ["guid", "link"])
def test_feed_items_have_valid_URLs(rss_feed_content, blog_url, element):
    """
    The items in the feed need to have valid urls in link and guid.

    As stated by W3 FEED Validator:
    * "link must be a full and valid URL"
    * "guid must be a full URL, unless isPermaLink attribute is false: /weblog/posts/the-minimal-server.html"
    """
    # This validation regex is taken from django.core.validators
    url_validation_regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        # domain...
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"  # localhost...
        # ...or ipv4
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        # ...or ipv6
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)" r"(?::\d+)?" r"(?:/?|[/?]\S+)$",  # optional port
        re.IGNORECASE,
    )

    def is_valid_URL(url):
        return url_validation_regex.match(url) is not None

    et = etree.parse(StringIO(rss_feed_content))
    channel = et.find("channel")
    item = channel.find("item")
    element = item.find(element)

    assert is_valid_URL(element.text)
    assert blog_url in element.text


@pytest.fixture(autouse=True)
def localeborg(default_locale):
    """
    LocaleBorg with default settings
    """
    LocaleBorg.reset()
    LocaleBorg.initialize({}, default_locale)
    try:
        yield
    finally:
        LocaleBorg.reset()


@pytest.fixture
def rss_feed_content(blog_url, config, default_locale):
    default_post = {
        "title": "post title",
        "slug": "awesome_article",
        "date": "2012-10-01 22:41",
        "author": None,
        "tags": "tags",
        "link": "link",
        "description": "description",
        "enclosure": "http://www.example.org/foo.mp3",
        "enclosure_length": "5",
    }
    meta_mock = mock.Mock(return_value=(defaultdict(str, default_post), None))
    with mock.patch("nikola.post.get_meta", meta_mock):
        with \
                mock.patch(
                    "nikola.nikola.utils.os.path.isdir", mock.Mock(return_value=True)), \
                mock.patch(
                    "nikola.nikola.Post.text", mock.Mock(return_value="some long text")
                ):
            with mock.patch(
                    "nikola.post.os.path.isfile", mock.Mock(return_value=True)):
                example_post = Post(
                    "source.file",
                    config,
                    "blog_folder",
                    True,
                    {"en": ""},
                    "post.tmpl",
                    FakeCompiler(),
                )

            filename = "testfeed.rss"
            opener_mock = mock.mock_open()

            with mock.patch("nikola.nikola.io.open", opener_mock, create=True):
                Nikola().generic_rss_renderer(
                    default_locale,
                    "blog_title",
                    blog_url,
                    "blog_description",
                    [example_post, ],
                    filename,
                    True,
                    False,
                )

            opener_mock.assert_called_once_with(filename, "w+", encoding="utf-8")

            # Python 3 / unicode strings workaround
            # lxml will complain if the encoding is specified in the
            # xml when running with unicode strings.
            # We do not include this in our content.
            file_content = [call[1][0] for call in opener_mock.mock_calls[2:-1]][0]
            splitted_content = file_content.split("\n")
            # encoding_declaration = splitted_content[0]
            content_without_encoding_declaration = splitted_content[1:]
            yield "\n".join(content_without_encoding_declaration)


@pytest.fixture
def config(blog_url, default_locale):
    fake_conf = defaultdict(str)
    fake_conf["TIMEZONE"] = "UTC"
    fake_conf["__tzinfo__"] = dateutil.tz.tzutc()
    fake_conf["DEFAULT_LANG"] = default_locale
    fake_conf["TRANSLATIONS"] = {default_locale: ""}
    fake_conf["BASE_URL"] = blog_url
    fake_conf["BLOG_AUTHOR"] = TranslatableSetting(
        "BLOG_AUTHOR", "Nikola Tesla", [default_locale]
    )
    fake_conf["TRANSLATIONS_PATTERN"] = "{path}.{lang}.{ext}"

    return fake_conf


@pytest.fixture
def blog_url():
    return "http://some.blog"


class FakeCompiler:
    demote_headers = False
    compile = None

    def extension(self):
        return ".html"

    def read_metadata(*args, **kwargs):
        return {}

    def register_extra_dependencies(self, post):
        pass
