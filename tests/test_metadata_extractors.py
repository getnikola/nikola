# -*- coding: utf-8 -*-
"""Test metadata extractors."""

import mock
import os
import pytest
from .base import FakeSite
from nikola.metadata_extractors import default_metadata_extractors_by, load_defaults, MetaCondition, check_conditions
from nikola.post import get_meta
from nikola.plugins.compile.rest import CompileRest
from nikola.plugins.compile.markdown import CompileMarkdown
from nikola.plugins.compile.ipynb import CompileIPynb
from nikola.plugins.compile.html import CompileHtml


@pytest.fixture(name='metadata_extractors_by')
def f__metadata_extractors_by():
    m = default_metadata_extractors_by()
    load_defaults(None, m)
    return m


class FakePost():
    def __init__(self, source_path, metadata_path, config, compiler, metadata_extractors_by):
        self.source_path = source_path
        self.metadata_path = metadata_path
        self.is_two_file = True
        self.config = {
            'TRANSLATIONS': {'en': './'},
            'DEFAULT_LANG': 'en'
        }
        self.config.update(config)
        self.default_lang = self.config['DEFAULT_LANG']
        self.metadata_extractors_by = metadata_extractors_by
        if compiler:
            self.compiler = compiler

    def translated_source_path(self, _):
        return self.source_path


class dummy():
    pass


@pytest.mark.parametrize("meta_twofile", [(1, "onefile", "twofile"), (2, "twofile", "onefile")])
@pytest.mark.parametrize("meta_format", [('nikola', 'Nikola'), ('toml', 'TOML'), ('yaml', 'YAML')])
def test_builtin_extractors_rest(metadata_extractors_by, meta_twofile, meta_format):
    twofile_number, twofile_expected, twofile_unexpected = meta_twofile
    twofile = twofile_number == 2
    format_lc, format_friendly = meta_format

    source_filename = "f-rest-{0}-{1}.rst".format(twofile_number, format_lc)
    metadata_filename = "f-rest-{0}-{1}.meta".format(twofile_number, format_lc)
    title = 'T: reST, {0}, {1}'.format(twofile_number, format_friendly)
    slug = "s-rest-{0}-{1}".format(twofile_number, format_lc)
    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'metadata_extractors', source_filename))
    metadata_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'metadata_extractors', metadata_filename))
    post = FakePost(source_path, metadata_path, {}, None, metadata_extractors_by)

    assert os.path.exists(source_path)
    if twofile:
        assert os.path.exists(metadata_path)

    meta, extractor = get_meta(post, None)

    assert meta
    if twofile:
        assert extractor is None
    else:
        assert extractor is metadata_extractors_by['name'][format_lc]

    assert meta['title'] == title
    assert meta['slug'] == slug
    assert twofile_expected in meta['tags']
    assert twofile_unexpected not in meta['tags']
    assert 'meta' in meta['tags']
    assert format_friendly in meta['tags']
    assert 'reST' in meta['tags']
    assert meta['date'] == '2017-07-01 00:00:00 UTC'


@pytest.mark.parametrize("meta_twofile", [(1, "onefile", "twofile"), (2, "twofile", "onefile")])
def test_nikola_meta_markdown(metadata_extractors_by, meta_twofile):
    twofile_number, twofile_expected, twofile_unexpected = meta_twofile
    twofile = twofile_number == 2

    source_filename = "f-markdown-{0}-nikola.md".format(twofile_number)
    metadata_filename = "f-markdown-{0}-nikola.meta".format(twofile_number)
    title = 'T: Markdown, {0}, Nikola'.format(twofile_number)
    slug = "s-markdown-{0}-nikola".format(twofile_number)
    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'metadata_extractors', source_filename))
    metadata_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'metadata_extractors', metadata_filename))
    post = FakePost(source_path, metadata_path, {}, None, metadata_extractors_by)

    assert os.path.exists(source_path)
    if twofile:
        assert os.path.exists(metadata_path)

    meta, extractor = get_meta(post, None)
    if twofile:
        assert extractor is None
    else:
        assert extractor is metadata_extractors_by['name']['nikola']

    assert meta['title'] == title
    assert meta['slug'] == slug
    assert twofile_expected in meta['tags']
    assert twofile_unexpected not in meta['tags']
    assert 'meta' in meta['tags']
    assert 'Nikola' in meta['tags']
    assert 'Markdown' in meta['tags']
    assert meta['date'] == '2017-07-01 00:00:00 UTC'


@pytest.mark.parametrize("compiler_data", [
    (CompileRest, 'rst', 'rest', 'reST'),
    (CompileMarkdown, 'md', 'markdown', 'Markdown'),
    (CompileIPynb, 'ipynb', 'ipynb', 'Jupyter Notebook'),
    (CompileHtml, 'html', 'html', 'HTML'),
])
def test_compiler_metadata(metadata_extractors_by, compiler_data):
    compiler_cls, compiler_ext, compiler_lc, compiler_name = compiler_data
    source_filename = "f-{0}-1-compiler.{1}".format(compiler_lc, compiler_ext)
    metadata_filename = "f-{0}-1-compiler.meta".format(compiler_lc)
    title = 'T: {0}, 1, compiler'.format(compiler_name)
    slug = "s-{0}-1-compiler".format(compiler_lc)
    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'metadata_extractors', source_filename))
    metadata_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'metadata_extractors', metadata_filename))

    config = {'USE_REST_DOCINFO_METADATA': True, 'MARKDOWN_EXTENSIONS': ['markdown.extensions.meta']}
    site = FakeSite()
    site.config.update(config)
    compiler_obj = compiler_cls()
    compiler_obj.set_site(site)

    post = FakePost(source_path, metadata_path, config, compiler_obj, metadata_extractors_by)

    class FakeBorg():
        current_lang = 'en'

        def __call__(self):
            return self

    with mock.patch('nikola.plugins.compile.' + compiler_lc + '.LocaleBorg', FakeBorg):
        meta, extractor = get_meta(post, None)

    assert meta['title'] == title
    assert meta['slug'] == slug
    assert 'meta' in meta['tags']
    assert 'onefile' in meta['tags']
    assert 'compiler' in meta['tags']
    assert compiler_name in meta['tags']
    assert meta['date'] == '2017-07-01 00:00:00 UTC'


def test_yaml_none_handling(metadata_extractors_by):
    yaml_extractor = metadata_extractors_by['name']['yaml']
    meta = yaml_extractor.extract_text("---\ntitle: foo\nslug: null")
    assert meta['title'] == 'foo'
    assert meta['slug'] == ''


def test_check_conditions():
    post = dummy()
    post.compiler = dummy()
    post.compiler.name = 'foo'
    filename = 'foo.bar'
    config = {'baz': True, 'quux': False}
    assert check_conditions(post, filename, [
        (MetaCondition.config_bool, 'baz'),
        (MetaCondition.config_present, 'quux')
    ], config, '')
    assert not check_conditions(post, filename, [
        (MetaCondition.config_bool, 'quux')
    ], config, '')
    assert not check_conditions(post, filename, [
        (MetaCondition.config_present, 'foobar')
    ], config, '')

    assert check_conditions(post, filename, [
        (MetaCondition.extension, 'bar')
    ], config, '')
    assert not check_conditions(post, filename, [
        (MetaCondition.extension, 'baz')
    ], config, '')

    assert check_conditions(post, filename, [
        (MetaCondition.compiler, 'foo')
    ], config, '')
    assert not check_conditions(post, filename, [
        (MetaCondition.compiler, 'foobar')
    ], config, '')

    assert not check_conditions(post, filename, [
        (MetaCondition.never, None),
        (MetaCondition.config_present, 'bar')
    ], config, '')
