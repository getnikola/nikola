# -*- coding: utf-8 -*-
# vim: set wrap textwidth=300

u"""Test shortcodes."""

from __future__ import unicode_literals
import pytest
from nikola import shortcodes
from .base import FakeSite

def noargs(site, data=''):
    return "noargs {0} success!".format(data)

def arg(*args, **kwargs):
    # don’t clutter the kwargs dict
    _ = kwargs.pop('site')
    data = kwargs.pop('data')
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
    # TODO: currently unsupported!
    # assert shortcodes.apply_shortcodes('test({{% arg "hello world" %}})', fakesite.shortcode_registry) == "test(arg ('hello world',)/[]/)"

def test_arg_keyword(fakesite):
    assert shortcodes.apply_shortcodes('test({{% arg 1a=2b %}})', fakesite.shortcode_registry) == "test(arg ()/[('1a', '2b')]/)"
    assert shortcodes.apply_shortcodes('test({{% arg 1a="2b 3c" 4d=5f %}})', fakesite.shortcode_registry) == "test(arg ()/[('1a', '2b 3c'), ('4d', '5f')]/)"

def test_data(fakesite):
    assert shortcodes.apply_shortcodes('test({{% arg 123 %}}Hello!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123',)/[]/Hello!)"
    assert shortcodes.apply_shortcodes('test({{% arg 123 456 foo=bar %}}Hello world!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123', '456')/[('foo', 'bar')]/Hello world!)"
    assert shortcodes.apply_shortcodes('test({{% arg 123 456 foo=bar baz="quotes rock." %}}Hello test suite!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123', '456')/[('baz', 'quotes rock.'), ('foo', 'bar')]/Hello test suite!)"
    # assert shortcodes.apply_shortcodes('test({{% arg "123 foo" foobar foo=bar baz="quotes rock." %}}Hello test suite!!{{% /arg %}})', fakesite.shortcode_registry) == "test(arg ('123 foo', 'foobar')/[('baz', 'quotes rock.'), ('foo', 'bar')]/Hello test suite!!)"
