import datetime
import unittest.mock

import dateutil
import pytest

from nikola.nikola import LEGAL_VALUES
from nikola.utils import (
    LocaleBorg,
    LocaleBorgUninitializedException,
    TranslatableSetting,
)

TESLA_BIRTHDAY = datetime.date(1856, 7, 10)
TESLA_BIRTHDAY_DT = datetime.datetime(1856, 7, 10, 12, 34, 56)
DT_EN_US = "July 10, 1856 at 12:34:56 PM UTC"
DT_PL = "10 lipca 1856 12:34:56 UTC"


@pytest.mark.parametrize("initial_lang", [None, ""])
def test_initilalize_failure(initial_lang):
    with pytest.raises(ValueError):
        LocaleBorg.initialize({}, initial_lang)

    assert not LocaleBorg.initialized


@pytest.mark.parametrize("initial_lang", ["en", "pl"])
def test_initialize(initial_lang):
    LocaleBorg.initialize({}, initial_lang)
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == initial_lang


def test_uninitialized_error():
    with pytest.raises(LocaleBorgUninitializedException):
        LocaleBorg()


@pytest.mark.parametrize(
    "locale, expected_current_lang",
    [
        ("pl", "pl"),
        pytest.param(
            "xx", "xx", id="fake language"
        ),  # used to ensure any locale can be supported
    ],
)
def test_set_locale(base_config, locale, expected_current_lang):
    LocaleBorg().set_locale(locale)
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == expected_current_lang


def test_set_locale_for_template():
    LocaleBorg.initialize({}, "en")
    assert LocaleBorg().set_locale("xz") == ""  # empty string for template ease of use


def test_format_date_webiso_basic(base_config):
    with unittest.mock.patch("babel.dates.format_datetime") as m:
        formatted_date = LocaleBorg().formatted_date("webiso", TESLA_BIRTHDAY_DT)
        assert formatted_date == "1856-07-10T12:34:56"
        m.assert_not_called()


@pytest.mark.parametrize("lang", ["en", "pl"])
def test_format_date_basic(base_config, lang):
    LocaleBorg.initialize({}, lang)
    formatted_date = LocaleBorg().formatted_date(
        "yyyy-MM-dd HH:mm:ss", TESLA_BIRTHDAY_DT
    )
    assert formatted_date == "1856-07-10 12:34:56"


def test_format_date_long(base_config):
    assert LocaleBorg().formatted_date("long", TESLA_BIRTHDAY_DT) == DT_EN_US
    assert LocaleBorg().formatted_date("long", TESLA_BIRTHDAY_DT, "en") == DT_EN_US
    assert LocaleBorg().formatted_date("long", TESLA_BIRTHDAY_DT, "pl") == DT_PL
    LocaleBorg().set_locale("pl")
    assert LocaleBorg().formatted_date("long", TESLA_BIRTHDAY_DT) == DT_PL
    assert LocaleBorg().formatted_date("long", TESLA_BIRTHDAY_DT, "en") == DT_EN_US


def test_format_date_timezone(base_config):
    tesla_150_birthday_dtz = datetime.datetime(
        2006, 7, 10, 12, 34, 56, tzinfo=dateutil.tz.gettz("America/New_York")
    )
    formatted_date = LocaleBorg().formatted_date("long", tesla_150_birthday_dtz)
    assert formatted_date == "July 10, 2006 at 12:34:56 PM -0400"

    nodst = datetime.datetime(
        2006, 1, 10, 12, 34, 56, tzinfo=dateutil.tz.gettz("America/New_York")
    )
    formatted_date = LocaleBorg().formatted_date("long", nodst)
    assert formatted_date == "January 10, 2006 at 12:34:56 PM -0500"


@pytest.mark.parametrize(
    "english_variant, expected_date",
    [
        pytest.param("en_US", DT_EN_US, id="US"),
        pytest.param("en_GB", "10 July 1856 at 12:34:56 UTC", id="GB"),
    ],
)
def test_format_date_locale_variants(english_variant, expected_date):
    LocaleBorg.initialize({"en": english_variant}, "en")
    assert LocaleBorg().formatted_date("long", TESLA_BIRTHDAY_DT, "en") == expected_date


@pytest.mark.parametrize(
    "lang, expected_string", [("en", "en July"), ("pl", "lipca pl")]
)
def test_format_date_translatablesetting(base_config, lang, expected_string):
    df = TranslatableSetting(
        "DATE_FORMAT", {"en": "'en' MMMM", "pl": "MMMM 'pl'"}, {"en": "", "pl": ""}
    )
    assert LocaleBorg().formatted_date(df, TESLA_BIRTHDAY_DT, lang) == expected_string


@pytest.mark.parametrize(
    "lang, expected_string",
    [
        pytest.param(None, "Foo July Bar", id="default"),
        pytest.param("pl", "Foo lipiec Bar", id="pl"),
    ],
)
def test_format_date_in_string_month(base_config, lang, expected_string):
    formatted_date = LocaleBorg().format_date_in_string(
        "Foo {month} Bar", TESLA_BIRTHDAY, lang
    )
    assert formatted_date == expected_string


@pytest.mark.parametrize(
    "lang, expected_string",
    [
        pytest.param(None, "Foo July 1856 Bar", id="default"),
        pytest.param("pl", "Foo lipiec 1856 Bar", id="pl"),
    ],
)
def test_format_date_in_string_month_year(base_config, lang, expected_string):
    formatted_date = LocaleBorg().format_date_in_string(
        "Foo {month_year} Bar", TESLA_BIRTHDAY, lang
    )
    assert formatted_date == expected_string


@pytest.mark.parametrize(
    "lang, expected_string",
    [
        pytest.param(None, "Foo July 10, 1856 Bar", id="default"),
        pytest.param("pl", "Foo 10 lipca 1856 Bar", id="pl"),
    ],
)
def test_format_date_in_string_month_day_year(base_config, lang, expected_string):
    formatted_date = LocaleBorg().format_date_in_string(
        "Foo {month_day_year} Bar", TESLA_BIRTHDAY, lang
    )
    assert formatted_date == expected_string


@pytest.mark.parametrize(
    "lang, expected_string",
    [
        pytest.param(None, "Foo 10 July 1856 Bar", id="default"),
        pytest.param("pl", "Foo 10 lipca 1856 Bar", id="pl"),
    ],
)
def test_format_date_in_string_month_day_year_gb(lang, expected_string):
    LocaleBorg.initialize({"en": "en_GB"}, "en")
    formatted_date = LocaleBorg().format_date_in_string(
        "Foo {month_day_year} Bar", TESLA_BIRTHDAY, lang
    )
    assert formatted_date == expected_string


@pytest.mark.parametrize(
    "message, expected_string",
    [
        ("Foo {month:'miesiąca' MMMM} Bar", "Foo miesiąca lipca Bar"),
        ("Foo {month_year:MMMM yyyy} Bar", "Foo lipca 1856 Bar"),
    ],
)
def test_format_date_in_string_customization(base_config, message, expected_string):
    formatted_date = LocaleBorg().format_date_in_string(message, TESLA_BIRTHDAY, "pl")
    assert formatted_date == expected_string


@pytest.mark.parametrize(
    "lang, expected_format",
    [("sr", "10. јул 1856. 12:34:56 UTC"), ("sr_latin", "10. jul 1856. 12:34:56 UTC")],
)
def test_locale_base(lang, expected_format):
    LocaleBorg.initialize(LEGAL_VALUES["LOCALES_BASE"], "en")
    formatted_date = LocaleBorg().formatted_date("long", TESLA_BIRTHDAY_DT, lang)
    assert formatted_date == expected_format


@pytest.fixture(autouse=True)
def localeborg_reset():
    """
    Reset the LocaleBorg before and after every test.
    """
    LocaleBorg.reset()
    assert not LocaleBorg.initialized
    try:
        yield
    finally:
        LocaleBorg.reset()
        assert not LocaleBorg.initialized


@pytest.fixture
def base_config():
    """A base config of LocaleBorg."""
    LocaleBorg.initialize({}, "en")
