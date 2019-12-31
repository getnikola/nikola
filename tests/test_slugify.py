"""Test slugify."""

import pytest

import nikola.utils


@pytest.mark.parametrize(
    "title, language, expected_slug",
    [
        pytest.param("hello", "en", "hello", id="ASCII"),
        pytest.param("hello-world", "en", "hello-world", id="ASCII with dashes"),
        pytest.param("hello world", "en", "hello-world", id="ASCII two words"),
        pytest.param("Hello World", "en", "hello-world", id="ASCII uppercase"),
        pytest.param(
            "The quick brown fox jumps over the lazy dog!-123.456",
            "en",
            "the-quick-brown-fox-jumps-over-the-lazy-dog-123456",
            id="ASCII with fancy characters",
        ),
        pytest.param(
            "zażółćgęśląjaźń",
            "pl",
            "zazolcgeslajazn",
            id="Polish diacritical characters",
        ),
        pytest.param(
            "zażółć-gęślą-jaźń",
            "pl",
            "zazolc-gesla-jazn",
            id="Polish diacritical characters and dashes",
        ),
        pytest.param(
            "Zażółć gęślą jaźń!-123.456",
            "pl",
            "zazolc-gesla-jazn-123456",
            id="Polish diacritical characters and fancy characters",
        ),
    ],
)
def test_slugify(title, language, expected_slug):
    o = nikola.utils.slugify(title, lang=language)
    assert o == expected_slug
    assert isinstance(o, str)


@pytest.mark.parametrize(
    "title, expected_slug",
    [
        pytest.param(
            u"Zażółć gęślą jaźń!-123.456", u"Zażółć gęślą jaźń!-123.456", id="polish"
        ),
        pytest.param(
            u'Zażółć gęślą jaźń!-123.456 "Hello World"?#H<e>l/l\\o:W\'o\rr*l\td|!\n',
            u"Zażółć gęślą jaźń!-123.456 -Hello World---H-e-l-l-o-W-o-r-l-d-!-",
            id="polish with banned characters",
        ),
    ],
)
def test_disarmed(disarm_slugify, title, expected_slug):
    """Test disarmed slugify."""
    o = nikola.utils.slugify(title, lang="pl")
    assert o == expected_slug
    assert isinstance(o, str)


@pytest.fixture
def disarm_slugify():
    nikola.utils.USE_SLUGIFY = False
    try:
        yield
    finally:
        nikola.utils.USE_SLUGIFY = True
