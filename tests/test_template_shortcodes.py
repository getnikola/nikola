"""Test template-based shortcodes."""

import pytest

from nikola import Nikola


def test_mixedargs(site):
    test_template = """
arg1: {{ _args[0] }}
arg2: {{ _args[1] }}
kwarg1: {{ kwarg1 }}
kwarg2: {{ kwarg2 }}
"""

    site.shortcode_registry["test1"] = site._make_renderfunc(test_template)
    site.shortcode_registry["test2"] = site._make_renderfunc(
        "Something completely different"
    )

    res = site.apply_shortcodes("{{% test1 kwarg1=spamm arg1 kwarg2=foo,bar arg2 %}}")[
        0
    ]

    assert res.strip() == """
arg1: arg1
arg2: arg2
kwarg1: spamm
kwarg2: foo,bar""".strip()


@pytest.mark.parametrize(
    "template, data, expected_result",
    [
        # one argument
        ("arg={{ _args[0] }}", "{{% test1 onearg %}}", "arg=onearg"),
        ("arg={{ _args[0] }}", '{{% test1 "one two" %}}', "arg=one two"),
        # keyword arguments
        ("foo={{ foo }}", "{{% test1 foo=bar %}}", "foo=bar"),
        ("foo={{ foo }}", '{{% test1 foo="bar baz" %}}', "foo=bar baz"),
        ("foo={{ foo }}", '{{% test1 foo="bar baz" spamm=ham %}}', "foo=bar baz"),
        # data
        (
            "data={{ data }}",
            "{{% test1 %}}spamm spamm{{% /test1 %}}",
            "data=spamm spamm",
        ),
        ("data={{ data }}", "{{% test1 spamm %}}", "data="),
        ("data={{ data }}", "{{% test1 data=dummy %}}", "data="),
    ],
)
def test_applying_shortcode(site, template, data, expected_result):
    site.shortcode_registry["test1"] = site._make_renderfunc(template)

    assert site.apply_shortcodes(data)[0] == expected_result


@pytest.fixture(scope="module")
def site():
    s = ShortcodeFakeSite()
    s.init_plugins()
    s._template_system = None
    return s


class ShortcodeFakeSite(Nikola):
    def _get_template_system(self):
        if self._template_system is None:
            # Load template plugin
            self._template_system = self.plugin_manager.getPluginByName(
                "jinja", "TemplateSystem"
            ).plugin_object
            self._template_system.set_directories(".", "cache")
            self._template_system.set_site(self)

        return self._template_system

    template_system = property(_get_template_system)
