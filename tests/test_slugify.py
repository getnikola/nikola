"""Test slugify."""

import pytest

import nikola.utils


@pytest.mark.parametrize("title, language, expected_slug", [
    ('hello', 'en', 'hello'),
    ('hello-world', 'en', 'hello-world'),
    ('hello world', 'en', 'hello-world'),
    ('Hello World', 'en', 'hello-world'),
    ('The quick brown fox jumps over the lazy dog!-123.456', 'en', 'the-quick-brown-fox-jumps-over-the-lazy-dog-123456'),
    ('zażółćgęśląjaźń', 'pl', 'zazolcgeslajazn'),
    ('zażółć-gęślą-jaźń', 'pl', 'zazolc-gesla-jazn'),
    ('Zażółć gęślą jaźń!-123.456', 'pl', 'zazolc-gesla-jazn-123456')
], ids=["ASCII", "ASCII with dashes", "ASCII two words", "ASCII uppercase",
        "ASCII with fancy characters", "Polish diacritical characters",
        "Polish diacritical characters and dashes",
        "Polish diacritical characters and fancy characters"])
def test_slugify(title, language, expected_slug):
    o = nikola.utils.slugify(title, lang=language)
    assert o == expected_slug
    assert isinstance(o, nikola.utils.unicode_str)


@pytest.mark.parametrize("title, expected_slug", [
    (u'Zażółć gęślą jaźń!-123.456', u'Zażółć gęślą jaźń!-123.456'),
    (u'Zażółć gęślą jaźń!-123.456 "Hello World"?#H<e>l/l\\o:W\'o\rr*l\td|!\n',
     u'Zażółć gęślą jaźń!-123.456 -Hello World---H-e-l-l-o-W-o-r-l-d-!-'),
], ids=["polish", "polish with banned characters"])
def test_disarmed(disarm_slugify, title, expected_slug):
    """Test disarmed slugify."""
    o = nikola.utils.slugify(title, lang='pl')
    assert o == expected_slug
    assert isinstance(o, nikola.utils.unicode_str)


@pytest.fixture
def disarm_slugify():
    nikola.utils.USE_SLUGIFY = False
    try:
        yield
    finally:
        nikola.utils.USE_SLUGIFY = True
