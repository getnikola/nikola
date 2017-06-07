# -*- coding: utf-8 -*-
# vim: set wrap textwidth=100
"""Test template-based shortcodes."""

from __future__ import unicode_literals

import pytest
from nikola import Nikola


class ShortcodeFakeSite(Nikola):
    def _get_template_system(self):
        if self._template_system is None:
            # Load template plugin
            self._template_system = self.plugin_manager.getPluginByName(
                'jinja', "TemplateSystem").plugin_object
            self._template_system.set_directories('.', 'cache')
            self._template_system.set_site(self)

        return self._template_system

    template_system = property(_get_template_system)


@pytest.fixture(scope="module")
def fakesite():
    s = ShortcodeFakeSite()
    s.init_plugins()
    s._template_system = None
    return s


def test_mixedargs(fakesite):
    TEST_TMPL = """
arg1: {{ _args[0] }}
arg2: {{ _args[1] }}
kwarg1: {{ kwarg1 }}
kwarg2: {{ kwarg2 }}
"""

    fakesite.shortcode_registry['test1'] = \
        fakesite._make_renderfunc(TEST_TMPL)
    fakesite.shortcode_registry['test2'] = \
        fakesite._make_renderfunc('Something completely different')

    res = fakesite.apply_shortcodes(
        '{{% test1 kwarg1=spamm arg1 kwarg2=foo,bar arg2 %}}')

    assert res.strip() == """
arg1: arg1
arg2: arg2
kwarg1: spamm
kwarg2: foo,bar""".strip()


def test_onearg(fakesite):
    fakesite.shortcode_registry['test1'] = \
        fakesite._make_renderfunc('arg={{ _args[0] }}')

    assert fakesite.apply_shortcodes('{{% test1 onearg %}}') == 'arg=onearg'
    assert fakesite.apply_shortcodes(
        '{{% test1 "one two" %}}') == 'arg=one two'


def test_kwarg(fakesite):
    fakesite.shortcode_registry['test1'] = \
        fakesite._make_renderfunc('foo={{ foo }}')

    res = fakesite.apply_shortcodes('{{% test1 foo=bar %}}')
    assert res == 'foo=bar'
    res = fakesite.apply_shortcodes('{{% test1 foo="bar baz" %}}')
    assert res == 'foo=bar baz'
    res = fakesite.apply_shortcodes('{{% test1 foo="bar baz" spamm=ham %}}')
    assert res == 'foo=bar baz'


def test_data(fakesite):
    fakesite.shortcode_registry['test1'] = \
        fakesite._make_renderfunc('data={{ data }}')

    res = fakesite.apply_shortcodes('{{% test1 %}}spamm spamm{{% /test1 %}}')
    assert res == 'data=spamm spamm'
    res = fakesite.apply_shortcodes('{{% test1 spamm %}}')
    assert res == 'data='
    # surprise!
    res = fakesite.apply_shortcodes('{{% test1 data=dummy %}}')
    assert res == 'data='
