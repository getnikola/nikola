"""Test shortcodes."""

import pytest

import nikola.utils
from nikola import shortcodes


@pytest.mark.parametrize(
    "template, expected_result",
    [
        ("test({{% noargs %}})", "test(noargs  success!)"),
        (
            "test({{% noargs %}}\\hello world/{{% /noargs %}})",
            "test(noargs \\hello world/ success!)",
        ),
    ],
)
def test_noargs(site, template, expected_result):
    applied_shortcode = shortcodes.apply_shortcodes(template, site.shortcode_registry)[0]
    assert applied_shortcode == expected_result


@pytest.mark.parametrize(
    "template, expected_result",
    [
        ("test({{% arg 1 %}})", "test(arg ('1',)/[]/)"),
        ("test({{% arg 1 2aa %}})", "test(arg ('1', '2aa')/[]/)"),
        ('test({{% arg "hello world" %}})', "test(arg ('hello world',)/[]/)"),
        ("test({{% arg back\\ slash arg2 %}})", "test(arg ('back slash', 'arg2')/[]/)"),
        ('test({{% arg "%}}" %}})', "test(arg ('%}}',)/[]/)"),
    ],
)
def test_positional_arguments(site, template, expected_result):
    applied_shortcode = shortcodes.apply_shortcodes(template, site.shortcode_registry)[0]
    assert applied_shortcode == expected_result


@pytest.mark.parametrize(
    "template, expected_result",
    [
        ("test({{% arg 1a=2b %}})", "test(arg ()/[('1a', '2b')]/)"),
        (
            'test({{% arg 1a="2b 3c" 4d=5f %}})',
            "test(arg ()/[('1a', '2b 3c'), ('4d', '5f')]/)",
        ),
        (
            'test({{% arg 1a="2b 3c" 4d=5f back=slash\\ slash %}})',
            "test(arg ()/[('1a', '2b 3c'), ('4d', '5f'), ('back', 'slash slash')]/)",
        ),
    ],
)
def test_arg_keyword(site, template, expected_result):
    applied_shortcode = shortcodes.apply_shortcodes(template, site.shortcode_registry)[0]
    assert applied_shortcode == expected_result


@pytest.mark.parametrize(
    "template, expected_result",
    [
        ("test({{% arg 123 %}}Hello!{{% /arg %}})", "test(arg ('123',)/[]/Hello!)"),
        (
            "test({{% arg 123 456 foo=bar %}}Hello world!{{% /arg %}})",
            "test(arg ('123', '456')/[('foo', 'bar')]/Hello world!)",
        ),
        (
            'test({{% arg 123 456 foo=bar baz="quotes rock." %}}Hello test suite!{{% /arg %}})',
            "test(arg ('123', '456')/[('baz', 'quotes rock.'), ('foo', 'bar')]/Hello test suite!)",
        ),
        (
            'test({{% arg "123 foo" foobar foo=bar baz="quotes rock." %}}Hello test suite!!{{% /arg %}})',
            "test(arg ('123 foo', 'foobar')/[('baz', 'quotes rock.'), ('foo', 'bar')]/Hello test suite!!)",
        ),
    ],
)
def test_data(site, template, expected_result):
    applied_shortcode = shortcodes.apply_shortcodes(template, site.shortcode_registry)[0]
    assert applied_shortcode == expected_result


@pytest.mark.parametrize(
    "template, expected_error_pattern",
    [
        (
            "{{% start",
            "^Shortcode 'start' starting at .* is not terminated correctly with '%}}'!",
        ),
        (
            "{{% wrong ending %%}",
            "^Syntax error in shortcode 'wrong' at .*: expecting whitespace!",
        ),
        (
            "{{% start %}} {{% /end %}}",
            "^Found shortcode ending '{{% /end %}}' which isn't closing a started shortcode",
        ),
        ('{{% start "asdf %}}', "^Unexpected end of unquoted string"),
        ("{{% start =b %}}", "^String starting at .* must be non-empty!"),
        ('{{% start "a\\', "^Unexpected end of data while escaping"),
        ("{{% start a\\", "^Unexpected end of data while escaping"),
        ('{{% start a"b" %}}', "^Unexpected quotation mark in unquoted string"),
        (
            '{{% start "a"b %}}',
            "^Syntax error in shortcode 'start' at .*: expecting whitespace!",
        ),
        ("{{% %}}", "^Syntax error: '{{%' must be followed by shortcode name"),
        ("{{%", "^Syntax error: '{{%' must be followed by shortcode name"),
        ("{{% ", "^Syntax error: '{{%' must be followed by shortcode name"),
        (
            "{{% / %}}",
            "^Found shortcode ending '{{% / %}}' which isn't closing a started shortcode",
        ),
        ("{{% / a %}}", "^Syntax error: '{{% /' must be followed by ' %}}'"),
        (
            "==> {{% <==",
            "^Shortcode '<==' starting at .* is not terminated correctly with '%}}'!",
        ),
    ],
)
def test_errors(site, template, expected_error_pattern):
    with pytest.raises(shortcodes.ParsingError, match=expected_error_pattern):
        shortcodes.apply_shortcodes(
            template, site.shortcode_registry, raise_exceptions=True
        )


@pytest.mark.parametrize(
    "input, expected",
    [
        ("{{% foo %}}", (u"SC1", {u"SC1": u"{{% foo %}}"})),
        (
            "{{% foo %}} bar {{% /foo %}}",
            (u"SC1", {u"SC1": u"{{% foo %}} bar {{% /foo %}}"}),
        ),
        (
            "AAA{{% foo %}} bar {{% /foo %}}BBB",
            (u"AAASC1BBB", {u"SC1": u"{{% foo %}} bar {{% /foo %}}"}),
        ),
        (
            "AAA{{% foo %}} {{% bar %}} {{% /foo %}}BBB",
            (u"AAASC1BBB", {u"SC1": u"{{% foo %}} {{% bar %}} {{% /foo %}}"}),
        ),
        (
            "AAA{{% foo %}} {{% /bar %}} {{% /foo %}}BBB",
            (u"AAASC1BBB", {u"SC1": u"{{% foo %}} {{% /bar %}} {{% /foo %}}"}),
        ),
        (
            "AAA{{% foo %}} {{% bar %}} quux {{% /bar %}} {{% /foo %}}BBB",
            (
                u"AAASC1BBB",
                {u"SC1": u"{{% foo %}} {{% bar %}} quux {{% /bar %}} {{% /foo %}}"},
            ),
        ),
        (
            "AAA{{% foo %}} BBB {{% bar %}} quux {{% /bar %}} CCC",
            (
                u"AAASC1 BBB SC2 CCC",
                {u"SC1": u"{{% foo %}}", u"SC2": u"{{% bar %}} quux {{% /bar %}}"},
            ),
        ),
    ],
)
def test_extract_shortcodes(input, expected, monkeypatch):
    i = iter("SC%d" % i for i in range(1, 100))
    monkeypatch.setattr(shortcodes, "_new_sc_id", i.__next__)
    extracted = shortcodes.extract_shortcodes(input)
    assert extracted == expected


@pytest.fixture(scope="module")
def site():
    s = FakeSiteWithShortcodeRegistry()
    s.register_shortcode("noargs", noargs)
    s.register_shortcode("arg", arg)
    return s


class FakeSiteWithShortcodeRegistry:
    def __init__(self):
        self.shortcode_registry = {}
        self.debug = True

    # this code duplicated in nikola/nikola.py
    def register_shortcode(self, name, f):
        """Register function f to handle shortcode "name"."""
        if name in self.shortcode_registry:
            nikola.utils.LOGGER.warn("Shortcode name conflict: %s", name)
            return
        self.shortcode_registry[name] = f


def noargs(site, data="", lang=""):
    return "noargs {0} success!".format(data)


def arg(*args, **kwargs):
    # don’t clutter the kwargs dict
    kwargs.pop("site")
    data = kwargs.pop("data")
    kwargs.pop("lang")
    return "arg {0}/{1}/{2}".format(args, sorted(kwargs.items()), data)
