# -*- coding: utf-8 -*-
# vim: set wrap textwidth=300

u"""Test shortcodes."""

from __future__ import unicode_literals
import pytest
from nikola import shortcodes
from .base import FakeSite, BaseTestCase
import sys

def noargs(site, data='', lang=''):
    return "noargs {0} success!".format(data)

def arg(*args, **kwargs):
    # don’t clutter the kwargs dict
    _ = kwargs.pop('site')
    data = kwargs.pop('data')
    lang = kwargs.pop('lang')
    # TODO hack for Python 2.7 -- remove when possible
    if sys.version_info[0] == 2:
        args = tuple(i.encode('utf-8') for i in args)
        kwargs = {k.encode('utf-8'): v.encode('utf-8') for k, v in kwargs.items()}
    return "arg {0}/{1}/{2}".format(args, sorted(kwargs.items()), data)


@pytest.fixture(scope="module")
def fakesite():
    s = FakeSite()
    s.register_shortcode('noargs', noargs)
    s.register_shortcode('arg', arg)
    return s

def test_noargs(fakesite):
    assert shortcodes.apply_shortcodes('test({{% noargs %}})', fakesite.shortcode_registry) == 'test(noargs  success!)'
    assert shortcodes.apply_shortcodes('test({{% noargs %}}\\hello world/{{% /noargs %}})', fakesite.shortcode_registry) == 'test(noargs \\hello world/ success!)'

def test_arg_pos(fakesite):
    assert shortcodes.apply_shortcodes('test({{% arg 1 %}})', fakesite.shortcode_registry) == "test(arg ('1',)/[]/)"
    assert shortcodes.apply_shortcodes('test({{% arg 1 2aa %}})', fakesite.shortcode_registry) == "test(arg ('1', '2aa')/[]/)"
    assert shortcodes.apply_shortcodes('test({{% arg "hello world" %}})', fakesite.shortcode_registry) == "test(arg ('hello world',)/[]/)"
    assert shortcodes.apply_shortcodes('test({{% arg back\ slash arg2 %}})', fakesite.shortcode_registry) == "test(arg ('back slash', 'arg2')/[]/)"
    assert shortcodes.apply_shortcodes('test({{% arg "%}}" %}})', fakesite.shortcode_registry) == "test(arg ('%}}',)/[]/)"

def test_arg_keyword(fakesite):
    assert shortcodes.apply_shortcodes('test({{% arg 1a=2b %}})', fakesite.shortcode_registry) == "test(arg ()/[('1a', '2b')]/)"
    assert shortcodes.apply_shortcodes('test({{% arg 1a="2b 3c" 4d=5f %}})', fakesite.shortcode_registry) == "test(arg ()/[('1a', '2b 3c'), ('4d', '5f')]/)"
    assert shortcodes.apply_shortcodes('test({{% arg 1a="2b 3c" 4d=5f back=slash\ slash %}})', fakesite.shortcode_registry) == "test(arg ()/[('1a', '2b 3c'), ('4d', '5f'), ('back', 'slash slash')]/)"

def test_data(fakesite):
    assert shortcodes.apply_shortcodes('test({{% arg 123 %}}Hello!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123',)/[]/Hello!)"
    assert shortcodes.apply_shortcodes('test({{% arg 123 456 foo=bar %}}Hello world!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123', '456')/[('foo', 'bar')]/Hello world!)"
    assert shortcodes.apply_shortcodes('test({{% arg 123 456 foo=bar baz="quotes rock." %}}Hello test suite!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123', '456')/[('baz', 'quotes rock.'), ('foo', 'bar')]/Hello test suite!)"
    assert shortcodes.apply_shortcodes('test({{% arg "123 foo" foobar foo=bar baz="quotes rock." %}}Hello test suite!!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123 foo', 'foobar')/[('baz', 'quotes rock.'), ('foo', 'bar')]/Hello test suite!!)"


class TestErrors(BaseTestCase):
    def setUp(self):
        self.fakesite = fakesite()

    def test_errors(self):
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Shortcode 'start' starting at .* is not terminated correctly with '%}}'!", shortcodes.apply_shortcodes, '{{% start', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Syntax error in shortcode 'wrong' at .*: expecting whitespace!", shortcodes.apply_shortcodes, '{{% wrong ending %%}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Found shortcode ending '{{% /end %}}' which isn't closing a started shortcode", shortcodes.apply_shortcodes, '{{% start %}} {{% /end %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Unexpected end of unquoted string", shortcodes.apply_shortcodes, '{{% start "asdf %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^String starting at .* must be non-empty!", shortcodes.apply_shortcodes, '{{% start =b %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Unexpected end of data while escaping", shortcodes.apply_shortcodes, '{{% start "a\\', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Unexpected end of data while escaping", shortcodes.apply_shortcodes, '{{% start a\\', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Unexpected quotation mark in unquoted string", shortcodes.apply_shortcodes, '{{% start a"b" %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Syntax error in shortcode 'start' at .*: expecting whitespace!", shortcodes.apply_shortcodes, '{{% start "a"b %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Syntax error: '{{%' must be followed by shortcode name", shortcodes.apply_shortcodes, '{{% %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Syntax error: '{{%' must be followed by shortcode name", shortcodes.apply_shortcodes, '{{%', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Syntax error: '{{%' must be followed by shortcode name", shortcodes.apply_shortcodes, '{{% ', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Found shortcode ending '{{% / %}}' which isn't closing a started shortcode", shortcodes.apply_shortcodes, '{{% / %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Syntax error: '{{% /' must be followed by ' %}}'", shortcodes.apply_shortcodes, '{{% / a %}}', self.fakesite.shortcode_registry, raise_exceptions=True)
        self.assertRaisesRegexp(shortcodes.ParsingError, "^Shortcode '<==' starting at .* is not terminated correctly with '%}}'!", shortcodes.apply_shortcodes, '==> {{% <==', self.fakesite.shortcode_registry, raise_exceptions=True)
