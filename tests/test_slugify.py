# -*- coding: utf-8 -*-

u"""Test slugify."""

from __future__ import unicode_literals
import nikola.utils


def test_ascii():
    """Test an ASCII-only string."""
    o = nikola.utils.slugify(u'hello', lang='en')
    assert o == u'hello'
    assert isinstance(o, nikola.utils.unicode_str)


def test_ascii_dash():
    """Test an ASCII string, with dashes."""
    o = nikola.utils.slugify(u'hello-world', lang='en')
    assert o == u'hello-world'
    assert isinstance(o, nikola.utils.unicode_str)


def test_ascii_fancy():
    """Test an ASCII string, with fancy characters."""
    o = nikola.utils.slugify(
        u'The quick brown fox jumps over the lazy dog!-123.456', lang='en')
    assert o == u'the-quick-brown-fox-jumps-over-the-lazy-dog-123456'
    assert isinstance(o, nikola.utils.unicode_str)


def test_pl():
    """Test a string with Polish diacritical characters."""
    o = nikola.utils.slugify(u'zażółćgęśląjaźń', lang='pl')
    assert o == u'zazolcgeslajazn'
    assert isinstance(o, nikola.utils.unicode_str)


def test_pl_dash():
    """Test a string with Polish diacritical characters and dashes."""
    o = nikola.utils.slugify(u'zażółć-gęślą-jaźń', lang='pl')
    assert o == u'zazolc-gesla-jazn'


def test_pl_fancy():
    """Test a string with Polish diacritical characters and fancy characters."""
    o = nikola.utils.slugify(u'Zażółć gęślą jaźń!-123.456', lang='pl')
    assert o == u'zazolc-gesla-jazn-123456'
    assert isinstance(o, nikola.utils.unicode_str)


def test_disarmed():
    """Test disarmed slugify."""
    nikola.utils.USE_SLUGIFY = False
    o = nikola.utils.slugify(u'Zażółć gęślą jaźń!-123.456', lang='pl')
    assert o == u'Zażółć gęślą jaźń!-123.456'
    assert isinstance(o, nikola.utils.unicode_str)
    nikola.utils.USE_SLUGIFY = True


def test_disarmed_weird():
    """Test disarmed slugify with banned characters."""
    nikola.utils.USE_SLUGIFY = False
    o = nikola.utils.slugify(
        u'Zażółć gęślą jaźń!-123.456 "Hello World"?#H<e>l/l\\o:W\'o\rr*l\td|!\n',
        lang='pl')
    assert o == u'Zażółć gęślą jaźń!-123.456 -Hello World---H-e-l-l-o-W-o-r-l-d-!-'
    assert isinstance(o, nikola.utils.unicode_str)
    nikola.utils.USE_SLUGIFY = True
