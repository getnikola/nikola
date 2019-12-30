"""Test metadata extractors."""

import os
from unittest import mock

import pytest

from nikola.metadata_extractors import (
    MetaCondition,
    check_conditions,
    default_metadata_extractors_by,
    load_defaults,
)
from nikola.plugins.compile.rest import CompileRest
from nikola.plugins.compile.markdown import CompileMarkdown
from nikola.plugins.compile.ipynb import CompileIPynb
from nikola.plugins.compile.html import CompileHtml
from nikola.post import get_meta

from .helper import FakeSite


@pytest.mark.parametrize(
    "filecount, expected, unexpected",
    [(1, "onefile", "twofile"), (2, "twofile", "onefile")],
)
@pytest.mark.parametrize(
    "format_lc, format_friendly",
    [("nikola", "Nikola"), ("toml", "TOML"), ("yaml", "YAML")],
)
def test_builtin_extractors_rest(
    metadata_extractors_by,
    testfiledir,
    filecount,
    expected,
    unexpected,
    format_lc,
    format_friendly,
):
    is_two_files = filecount == 2

    source_filename = "f-rest-{0}-{1}.rst".format(filecount, format_lc)
    metadata_filename = "f-rest-{0}-{1}.meta".format(filecount, format_lc)
    source_path = os.path.join(testfiledir, source_filename)
    metadata_path = os.path.join(testfiledir, metadata_filename)
    post = FakePost(source_path, metadata_path, {}, None, metadata_extractors_by)

    assert os.path.exists(source_path)
    if is_two_files:
        assert os.path.exists(metadata_path)

    meta, extractor = get_meta(post, None)

    assert meta
    assert extractor is metadata_extractors_by["name"][format_lc]

    assert meta["title"] == "T: reST, {0}, {1}".format(filecount, format_friendly)
    assert meta["slug"] == "s-rest-{0}-{1}".format(filecount, format_lc)
    assert expected in meta["tags"]
    assert unexpected not in meta["tags"]
    assert "meta" in meta["tags"]
    assert format_friendly in meta["tags"]
    assert "reST" in meta["tags"]
    assert meta["date"] == "2017-07-01 00:00:00 UTC"


@pytest.mark.parametrize(
    "filecount, expected, unexpected",
    [(1, "onefile", "twofile"), (2, "twofile", "onefile")],
)
def test_nikola_meta_markdown(
    metadata_extractors_by, testfiledir, filecount, expected, unexpected
):
    is_two_files = filecount == 2

    source_filename = "f-markdown-{0}-nikola.md".format(filecount)
    metadata_filename = "f-markdown-{0}-nikola.meta".format(filecount)
    source_path = os.path.join(testfiledir, source_filename)
    metadata_path = os.path.join(testfiledir, metadata_filename)
    post = FakePost(source_path, metadata_path, {}, None, metadata_extractors_by)

    assert os.path.exists(source_path)
    if is_two_files:
        assert os.path.exists(metadata_path)

    meta, extractor = get_meta(post, None)
    assert extractor is metadata_extractors_by["name"]["nikola"]

    assert meta["title"] == "T: Markdown, {0}, Nikola".format(filecount)
    assert meta["slug"] == "s-markdown-{0}-nikola".format(filecount)
    assert expected in meta["tags"]
    assert unexpected not in meta["tags"]
    assert "meta" in meta["tags"]
    assert "Nikola" in meta["tags"]
    assert "Markdown" in meta["tags"]
    assert meta["date"] == "2017-07-01 00:00:00 UTC"


@pytest.mark.parametrize(
    "compiler, fileextension, compiler_lc, name",
    [
        (CompileRest, "rst", "rest", "reST"),
        (CompileMarkdown, "md", "markdown", "Markdown"),
        (CompileIPynb, "ipynb", "ipynb", "Jupyter Notebook"),
        (CompileHtml, "html", "html", "HTML"),
    ],
)
def test_compiler_metadata(
    metadata_extractors_by, testfiledir, compiler, fileextension, compiler_lc, name
):
    source_filename = "f-{0}-1-compiler.{1}".format(compiler_lc, fileextension)
    metadata_filename = "f-{0}-1-compiler.meta".format(compiler_lc)
    title = "T: {0}, 1, compiler".format(name)
    slug = "s-{0}-1-compiler".format(compiler_lc)
    source_path = os.path.join(testfiledir, source_filename)
    metadata_path = os.path.join(testfiledir, metadata_filename)

    config = {
        "USE_REST_DOCINFO_METADATA": True,
        "MARKDOWN_EXTENSIONS": ["markdown.extensions.meta"],
    }
    site = FakeSite()
    site.config.update(config)
    compiler_obj = compiler()
    compiler_obj.set_site(site)

    post = FakePost(
        source_path, metadata_path, config, compiler_obj, metadata_extractors_by
    )

    class FakeBorg:
        current_lang = "en"

        def __call__(self):
            return self

    with mock.patch("nikola.plugins.compile." + compiler_lc + ".LocaleBorg", FakeBorg):
        meta, extractor = get_meta(post, None)

    assert meta["title"] == title
    assert meta["slug"] == slug
    assert "meta" in meta["tags"]
    assert "onefile" in meta["tags"]
    assert "compiler" in meta["tags"]
    assert name in meta["tags"]
    assert meta["date"] == "2017-07-01 00:00:00 UTC"


def test_yaml_none_handling(metadata_extractors_by):
    yaml_extractor = metadata_extractors_by["name"]["yaml"]
    meta = yaml_extractor.extract_text("---\ntitle: foo\nslug: null")
    assert meta["title"] == "foo"
    assert meta["slug"] == ""


@pytest.mark.parametrize(
    "conditions",
    [
        [(MetaCondition.config_bool, "baz"), (MetaCondition.config_present, "quux")],
        pytest.param(
            [(MetaCondition.config_bool, "quux")], marks=pytest.mark.xfail(strict=True)
        ),
        pytest.param(
            [(MetaCondition.config_present, "foobar")],
            marks=pytest.mark.xfail(strict=True),
        ),
        [(MetaCondition.extension, "bar")],
        pytest.param(
            [(MetaCondition.extension, "baz")], marks=pytest.mark.xfail(strict=True)
        ),
        [(MetaCondition.compiler, "foo")],
        pytest.param(
            [(MetaCondition.compiler, "foobar")], marks=pytest.mark.xfail(strict=True)
        ),
        pytest.param(
            [(MetaCondition.never, None), (MetaCondition.config_present, "bar")],
            marks=pytest.mark.xfail(strict=True),
        ),
    ],
)
def test_check_conditions(conditions, dummy_post):
    filename = "foo.bar"
    config = {"baz": True, "quux": False}
    assert check_conditions(dummy_post, filename, conditions, config, "")


class FakePost:
    def __init__(
        self, source_path, metadata_path, config, compiler, metadata_extractors_by
    ):
        self.source_path = source_path
        self.metadata_path = metadata_path
        self.is_two_file = True
        self.config = {"TRANSLATIONS": {"en": "./"}, "DEFAULT_LANG": "en"}
        self.config.update(config)
        self.default_lang = self.config["DEFAULT_LANG"]
        self.metadata_extractors_by = metadata_extractors_by
        if compiler:
            self.compiler = compiler

    def translated_source_path(self, _):
        return self.source_path


@pytest.fixture
def metadata_extractors_by():
    metadata_extractors = default_metadata_extractors_by()
    load_defaults(None, metadata_extractors)
    return metadata_extractors


@pytest.fixture(scope="module")
def testfiledir(test_dir):
    return os.path.join(test_dir, "data", "metadata_extractors")


@pytest.fixture(scope="module")
def dummy_post():
    class DummyCompiler:
        name = "foo"

    class DummyPost:
        compiler = DummyCompiler()

    return DummyPost()
