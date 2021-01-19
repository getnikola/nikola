"""
Testing Nikolas utility functions.
"""

import os
from unittest import mock

import pytest
import lxml.html

from nikola import metadata_extractors
from nikola.plugins.task.sitemap import get_base_path as sitemap_get_base_path
from nikola.post import get_meta
from nikola.utils import (
    TemplateHookRegistry,
    TranslatableSetting,
    demote_headers,
    get_asset_path,
    get_crumbs,
    get_theme_chain,
    get_translation_candidate,
    write_metadata,
    bool_from_meta,
)


def test_getting_metadata_from_content(post):
    post.source_path = "file_with_metadata"
    post.metadata_path = "file_with_metadata.meta"

    file_content = """\
.. title: Nikola needs more tests!
.. slug: write-tests-now
.. date: 2012/09/15 19:52:05
.. tags:
.. link:
.. description:

Post content
"""
    opener_mock = mock.mock_open(read_data=file_content)
    with mock.patch("nikola.post.io.open", opener_mock, create=True):
        meta = get_meta(post, None)[0]

    assert "Nikola needs more tests!" == meta["title"]
    assert "write-tests-now" == meta["slug"]
    assert "2012/09/15 19:52:05" == meta["date"]
    assert "tags" not in meta
    assert "link" not in meta
    assert "description" not in meta


def test_get_title_from_fname(post):
    post.source_path = "file_with_metadata"
    post.metadata_path = "file_with_metadata.meta"

    file_content = """\
.. slug: write-tests-now
.. date: 2012/09/15 19:52:05
.. tags:
.. link:
.. description:
"""
    opener_mock = mock.mock_open(read_data=file_content)
    with mock.patch("nikola.post.io.open", opener_mock, create=True):
        meta = get_meta(post, None)[0]

    assert "file_with_metadata" == meta["title"]
    assert "write-tests-now" == meta["slug"]
    assert "2012/09/15 19:52:05" == meta["date"]
    assert "tags" not in meta
    assert "link" not in meta
    assert "description" not in meta


def test_use_filename_as_slug_fallback(post):
    post.source_path = "Slugify this"
    post.metadata_path = "Slugify this.meta"

    file_content = """\
.. title: Nikola needs more tests!
.. date: 2012/09/15 19:52:05
.. tags:
.. link:
.. description:

Post content
"""
    opener_mock = mock.mock_open(read_data=file_content)
    with mock.patch("nikola.post.io.open", opener_mock, create=True):
        meta = get_meta(post, None)[0]

    assert "Nikola needs more tests!" == meta["title"]
    assert "slugify-this" == meta["slug"]
    assert "2012/09/15 19:52:05" == meta["date"]
    assert "tags" not in meta
    assert "link" not in meta
    assert "description" not in meta


@pytest.mark.parametrize(
    "unslugify, expected_title", [(True, "Dub dub title"), (False, "dub_dub_title")]
)
def test_extracting_metadata_from_filename(post, unslugify, expected_title):
    post.source_path = "2013-01-23-the_slug-dub_dub_title.md"
    post.metadata_path = "2013-01-23-the_slug-dub_dub_title.meta"

    post.config[
        "FILE_METADATA_REGEXP"
    ] = r"(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.*)-(?P<title>.*)\.md"
    post.config["FILE_METADATA_UNSLUGIFY_TITLES"] = unslugify

    no_metadata_opener = mock.mock_open(read_data="No metadata in the file!")
    with mock.patch("nikola.post.io.open", no_metadata_opener, create=True):
        meta = get_meta(post, None)[0]

    assert expected_title == meta["title"]
    assert "the_slug" == meta["slug"]
    assert "2013-01-23" == meta["date"]


def test_get_meta_slug_only_from_filename(post):
    post.source_path = "some/path/the_slug.md"
    post.metadata_path = "some/path/the_slug.meta"

    no_metadata_opener = mock.mock_open(read_data="No metadata in the file!")
    with mock.patch("nikola.post.io.open", no_metadata_opener, create=True):
        meta = get_meta(post, None)[0]

    assert "the_slug" == meta["slug"]


@pytest.mark.parametrize(
    "level, input_str, expected_output",
    [
        pytest.param(
            0,
            """
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     """,
            """
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     """,
            id="by zero",
        ),
        pytest.param(
            1,
            """
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     """,
            """
     <h2>header 1</h2>
     <h3>header 2</h3>
     <h4>header 3</h4>
     <h5>header 4</h5>
     <h6>header 5</h6>
     <h6>header 6</h6>
     """,
            id="by one",
        ),
        pytest.param(
            2,
            """
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     """,
            """
     <h3>header 1</h3>
     <h4>header 2</h4>
     <h5>header 3</h5>
     <h6>header 4</h6>
     <h6>header 5</h6>
     <h6>header 6</h6>
     """,
            id="by two",
        ),
        pytest.param(
            -1,
            """
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     """,
            """
     <h1>header 1</h1>
     <h1>header 2</h1>
     <h2>header 3</h2>
     <h3>header 4</h3>
     <h4>header 5</h4>
     <h5>header 6</h5>
     """,
            id="by minus one",
        ),
    ],
)
def test_demoting_headers(level, input_str, expected_output):
    doc = lxml.html.fromstring(input_str)
    outdoc = lxml.html.fromstring(expected_output)
    demote_headers(doc, level)
    assert lxml.html.tostring(outdoc) == lxml.html.tostring(doc)


def test_TranslatableSettingsTest_with_string_input():
    """Test ing translatable settings with string input."""
    inp = "Fancy Blog"
    setting = TranslatableSetting("TestSetting", inp, {"xx": ""})
    setting.default_lang = "xx"
    setting.lang = "xx"

    assert inp == str(setting)
    assert inp == setting()  # no language specified
    assert inp == setting("xx")  # real language specified
    assert inp == setting("zz")  # fake language specified
    assert setting.lang == "xx"
    assert setting.default_lang == "xx"


def test_TranslatableSetting_with_dict_input():
    """Tests for translatable setting with dict input."""
    inp = {"xx": "Fancy Blog", "zz": "Schmancy Blog"}

    setting = TranslatableSetting("TestSetting", inp, {"xx": "", "zz": ""})
    setting.default_lang = "xx"
    setting.lang = "xx"

    assert inp["xx"] == str(setting)
    assert inp["xx"] == setting()  # no language specified
    assert inp["xx"] == setting("xx")  # real language specified
    assert inp["zz"] == setting("zz")  # fake language specified
    assert inp["xx"] == setting("ff")


def test_TranslatableSetting_with_language_change():
    """Test translatable setting with language change along the way."""
    inp = {"xx": "Fancy Blog", "zz": "Schmancy Blog"}

    setting = TranslatableSetting("TestSetting", inp, {"xx": "", "zz": ""})
    setting.default_lang = "xx"
    setting.lang = "xx"

    assert inp["xx"] == str(setting)
    assert inp["xx"] == setting()

    # Change the language.
    # WARNING: DO NOT set lang locally in real code!  Set it globally
    #          instead! (TranslatableSetting.lang = ...)
    # WARNING: TranslatableSetting.lang is used to override the current
    #          locale settings returned by LocaleBorg!  Use with care!
    setting.lang = "zz"

    assert inp["zz"] == str(setting)
    assert inp["zz"] == setting()


@pytest.mark.parametrize(
    "path, files_folders, expected_path_end",
    [
        (
            "assets/css/nikola_rst.css",
            {"files": ""},  # default files_folders
            "nikola/data/themes/base/assets/css/nikola_rst.css",
        ),
        (
            "assets/css/theme.css",
            {"files": ""},  # default files_folders
            "nikola/data/themes/bootstrap4/assets/css/theme.css",
        ),
        ("nikola.py", {"nikola": ""}, "nikola/nikola.py"),
        ("nikola/nikola.py", {"nikola": "nikola"}, "nikola/nikola.py"),
        ("nikola.py", {"nikola": "nikola"}, None),
    ],
)
def test_get_asset_path(path, files_folders, expected_path_end):
    theme_chain = get_theme_chain("bootstrap4", ["themes"])
    asset_path = get_asset_path(path, theme_chain, files_folders)

    if expected_path_end:
        asset_path = asset_path.replace("\\", "/")
        assert asset_path.endswith(expected_path_end)
    else:
        assert asset_path is None


@pytest.mark.parametrize(
    "path, is_file, expected_crumbs",
    [
        ("galleries", False, [["#", "galleries"]]),
        (
            os.path.join("galleries", "demo"),
            False,
            [["..", "galleries"], ["#", "demo"]],
        ),
        (
            os.path.join("listings", "foo", "bar"),
            True,
            [["..", "listings"], [".", "foo"], ["#", "bar"]],
        ),
    ],
)
def test_get_crumbs(path, is_file, expected_crumbs):
    crumbs = get_crumbs(path, is_file=is_file)
    assert len(crumbs) == len(expected_crumbs)
    for crumb, expected_crumb in zip(crumbs, expected_crumbs):
        assert crumb == expected_crumb


@pytest.mark.parametrize(
    "pattern, path, lang, expected_path",
    [
        ("{path}.{lang}.{ext}", "*.rst", "es", "*.es.rst"),
        ("{path}.{lang}.{ext}", "fancy.post.rst", "es", "fancy.post.es.rst"),
        ("{path}.{lang}.{ext}", "*.es.rst", "es", "*.es.rst"),
        ("{path}.{lang}.{ext}", "*.es.rst", "en", "*.rst"),
        (
            "{path}.{lang}.{ext}",
            "cache/posts/fancy.post.es.html",
            "en",
            "cache/posts/fancy.post.html",
        ),
        (
            "{path}.{lang}.{ext}",
            "cache/posts/fancy.post.html",
            "es",
            "cache/posts/fancy.post.es.html",
        ),
        (
            "{path}.{lang}.{ext}",
            "cache/pages/charts.html",
            "es",
            "cache/pages/charts.es.html",
        ),
        (
            "{path}.{lang}.{ext}",
            "cache/pages/charts.html",
            "en",
            "cache/pages/charts.html",
        ),
        ("{path}.{ext}.{lang}", "*.rst", "es", "*.rst.es"),
        ("{path}.{ext}.{lang}", "*.rst.es", "es", "*.rst.es"),
        ("{path}.{ext}.{lang}", "*.rst.es", "en", "*.rst"),
        (
            "{path}.{ext}.{lang}",
            "cache/posts/fancy.post.html.es",
            "en",
            "cache/posts/fancy.post.html",
        ),
        (
            "{path}.{ext}.{lang}",
            "cache/posts/fancy.post.html",
            "es",
            "cache/posts/fancy.post.html.es",
        ),
    ],
)
def test_get_translation_candidate(pattern, path, lang, expected_path):
    config = {
        "TRANSLATIONS_PATTERN": pattern,
        "DEFAULT_LANG": "en",
        "TRANSLATIONS": {"es": "1", "en": 1},
    }
    assert get_translation_candidate(config, path, lang) == expected_path


def test_TemplateHookRegistry():
    r = TemplateHookRegistry("foo", None)
    r.append("Hello!")
    r.append(lambda x: "Hello " + x + "!", False, "world")
    assert r() == "Hello!\nHello world!"


@pytest.mark.parametrize(
    "base, expected_path",
    [
        ("http://some.site", "/"),
        ("http://some.site/", "/"),
        ("http://some.site/some/sub-path", "/some/sub-path/"),
        ("http://some.site/some/sub-path/", "/some/sub-path/"),
    ],
)
def test_sitemap_get_base_path(base, expected_path):
    assert expected_path == sitemap_get_base_path(base)


@pytest.mark.parametrize(
    "metadata_format, expected_result",
    [
        (
            "nikola",
            """\
.. title: Hello, world!
.. slug: hello-world
.. a: 1
.. b: 2

""",
        ),
        (
            "yaml",
            """\
---
a: '1'
b: '2'
slug: hello-world
title: Hello, world!
---
""",
        ),
    ],
)
def test_write_metadata_with_formats(metadata_format, expected_result):
    """
    Test writing metadata with different formats.

    YAML is expected to be sorted alphabetically.
    Nikola sorts by putting the defaults first and then sorting the rest
    alphabetically.
    """
    data = {"slug": "hello-world", "title": "Hello, world!", "b": "2", "a": "1"}
    assert write_metadata(data, metadata_format) == expected_result


def test_write_metadata_with_format_toml():
    """
    Test writing metadata in TOML format.

    TOML is sorted randomly in Python 3.5 or older and by insertion
    order since Python 3.6.
    """
    data = {"slug": "hello-world", "title": "Hello, world!", "b": "2", "a": "1"}

    toml = write_metadata(data, "toml")
    assert toml.startswith("+++\n")
    assert toml.endswith("+++\n")
    assert 'slug = "hello-world"' in toml
    assert 'title = "Hello, world!"' in toml
    assert 'b = "2"' in toml
    assert 'a = "1"' in toml


@pytest.mark.parametrize(
    "wrap, expected_result",
    [
        (
            False,
            """\
.. title: Hello, world!
.. slug: hello-world

""",
        ),
        (
            True,
            """\
<!--
.. title: Hello, world!
.. slug: hello-world
-->

""",
        ),
        (
            ("111", "222"),
            """\
111
.. title: Hello, world!
.. slug: hello-world
222

""",
        ),
    ],
)
def test_write_metadata_comment_wrap(wrap, expected_result):
    data = {"title": "Hello, world!", "slug": "hello-world"}
    assert write_metadata(data, "nikola", wrap) == expected_result


@pytest.mark.parametrize(
    "metadata_format, expected_results",
    [
        (
            "rest_docinfo",
            [
                """=============
Hello, world!
=============

:slug: hello-world
"""
            ],
        ),
        (
            "markdown_meta",
            [
                """title: Hello, world!
slug: hello-world

""",
                """slug: hello-world
title: Hello, world!

""",
            ],
        ),
    ],
)
def test_write_metadata_compiler(metadata_format, expected_results):
    """
    Test writing metadata with different formats.

    We test for multiple results because some compilers might produce
    unordered output.
    """
    data = {"title": "Hello, world!", "slug": "hello-world"}
    assert write_metadata(data, metadata_format) in expected_results


@pytest.mark.parametrize(
    "post_format, expected_metadata",
    [
        ("rest", "==\nxx\n==\n\n"),
        ("markdown", "title: xx\n\n"),
        ("html", ".. title: xx\n\n"),
    ],
)
def test_write_metadata_pelican_detection(post, post_format, expected_metadata):
    post.name = post_format

    data = {"title": "xx"}
    assert write_metadata(data, "pelican", compiler=post) == expected_metadata


def test_write_metadata_pelican_detection_default():
    data = {"title": "xx"}
    assert write_metadata(data, "pelican", compiler=None) == ".. title: xx\n\n"


def test_write_metadata_from_site(post):
    post.config = {"METADATA_FORMAT": "yaml"}
    data = {"title": "xx"}
    assert write_metadata(data, site=post) == "---\ntitle: xx\n---\n"


def test_write_metadata_default(post):
    data = {"title": "xx"}
    assert write_metadata(data) == ".. title: xx\n\n"


@pytest.mark.parametrize("arg", ["foo", "filename_regex"])
def test_write_metadata_fallbacks(post, arg):
    data = {"title": "xx"}
    assert write_metadata(data, arg) == ".. title: xx\n\n"


@pytest.mark.parametrize("value, expected", [
    ("true", True),
    ("True", True),
    ("TRUE", True),
    ("yes", True),
    ("Yes", True),
    ("YES", True),
    ("false", False),
    ("False", False),
    ("FALSE", False),
    ("no", False),
    ("No", False),
    ("NO", False),
    ("1", True),
    (1, True),
    ("0", False),
    (0, False),
    ("0", False),
    (True, True),
    (False, False),
    ("unknown", "F"),
    (None, "B"),
    ("", "B"),
])
def test_bool_from_meta(value, expected):
    meta = {"key": value}
    assert bool_from_meta(meta, "key", "F", "B") == expected


@pytest.fixture
def post():
    return FakePost()


class FakePost:
    default_lang = "en"
    metadata_extractors_by = metadata_extractors.default_metadata_extractors_by()
    config = {
        "TRANSLATIONS_PATTERN": "{path}.{lang}.{ext}",
        "TRANSLATIONS": {"en": "./"},
        "DEFAULT_LANG": "en",
    }

    def __init__(self):
        metadata_extractors.load_defaults(self, self.metadata_extractors_by)
