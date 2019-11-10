import datetime
import dateutil
import unittest.mock

import pytest

from nikola.nikola import LEGAL_VALUES
from nikola.utils import (
    LocaleBorg, LocaleBorgUninitializedException, TranslatableSetting)

TESLA_BIRTHDAY = datetime.date(1856, 7, 10)
TESLA_BIRTHDAY_DT = datetime.datetime(1856, 7, 10, 12, 34, 56)
DT_EN_US = 'July 10, 1856 at 12:34:56 PM UTC'
DT_PL = '10 lipca 1856 12:34:56 UTC'


@pytest.mark.parametrize("initial_lang", [None, ''])
def test_initilalize_failure(initial_lang):
    with pytest.raises(ValueError):
        LocaleBorg.initialize({}, initial_lang)

    assert not LocaleBorg.initialized


@pytest.mark.parametrize("initial_lang", ['en', 'pl'])
def test_initialize(initial_lang):
    LocaleBorg.initialize({}, initial_lang)
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == initial_lang


def test_uninitialized_error():
    with pytest.raises(LocaleBorgUninitializedException):
        LocaleBorg()


@pytest.mark.parametrize("locale, expected_current_lang", [
    ('pl', 'pl'),
    ('xx', 'xx'),  # fake language -- used to ensure any locale can be supported
])
def test_set_locale(base_config, locale, expected_current_lang):
    LocaleBorg().set_locale(locale)
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == expected_current_lang


def test_set_locale_for_template():
    LocaleBorg.initialize({}, 'en')
    assert LocaleBorg().set_locale('xz') == ''  # empty string for template ease of use


def test_format_date_webiso_basic(base_config):
    with unittest.mock.patch('babel.dates.format_datetime') as m:
        assert LocaleBorg().formatted_date('webiso', TESLA_BIRTHDAY_DT) == '1856-07-10T12:34:56'
        m.assert_not_called()


@pytest.mark.parametrize("lang", ["en", "pl"])
def test_format_date_basic(base_config, lang):
    LocaleBorg.initialize({}, lang)
    assert LocaleBorg().formatted_date('YYYY-MM-dd HH:mm:ss', TESLA_BIRTHDAY_DT) == '1856-07-10 12:34:56'


def test_format_date_long(base_config):
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT) == DT_EN_US
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'en') == DT_EN_US
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'pl') == DT_PL
    LocaleBorg().set_locale('pl')
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT) == DT_PL
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'en') == DT_EN_US


def test_format_date_timezone(base_config):
    tesla_150_birthday_dtz = datetime.datetime(2006, 7, 10, 12, 34, 56, tzinfo=dateutil.tz.gettz('America/New_York'))
    assert LocaleBorg().formatted_date('long', tesla_150_birthday_dtz) == 'July 10, 2006 at 12:34:56 PM -0400'
    nodst = datetime.datetime(2006, 1, 10, 12, 34, 56, tzinfo=dateutil.tz.gettz('America/New_York'))
    assert LocaleBorg().formatted_date('long', nodst) == 'January 10, 2006 at 12:34:56 PM -0500'


@pytest.mark.parametrize("english_variant, expected_date", [
    ('en_US', DT_EN_US),
    ('en_GB', '10 July 1856 at 12:34:56 UTC'),
], ids=["US", "GB"])
def test_format_date_locale_variants(english_variant, expected_date):
    LocaleBorg.initialize({'en': english_variant}, 'en')
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'en') == expected_date


@pytest.mark.parametrize("lang, expected_string", [
    ('en', 'en July'),
    ('pl', 'lipca pl')
])
def test_format_date_translatablesetting(base_config, lang, expected_string):
    df = TranslatableSetting("DATE_FORMAT", {'en': "'en' MMMM", 'pl': "MMMM 'pl'"}, {'en': '', 'pl': ''})
    assert LocaleBorg().formatted_date(df, TESLA_BIRTHDAY_DT, lang) == expected_string


@pytest.mark.parametrize("lang, expected_string", [
    (None, 'Foo July Bar'),
    ('pl', 'Foo lipiec Bar')
], ids=["default", "pl"])
def test_format_date_in_string_month(base_config, lang, expected_string):
    assert LocaleBorg().format_date_in_string("Foo {month} Bar", TESLA_BIRTHDAY, lang) == expected_string


@pytest.mark.parametrize("lang, expected_string", [
    (None, 'Foo July 1856 Bar'),
    ('pl', 'Foo lipiec 1856 Bar')
], ids=["default", "pl"])
def test_format_date_in_string_month_year(base_config, lang, expected_string):
    assert LocaleBorg().format_date_in_string("Foo {month_year} Bar", TESLA_BIRTHDAY, lang) == expected_string


@pytest.mark.parametrize("lang, expected_string", [
    (None, 'Foo July 10, 1856 Bar'),
    ('pl', 'Foo 10 lipca 1856 Bar')
], ids=["default", "pl"])
def test_format_date_in_string_month_day_year(base_config, lang, expected_string):
    assert LocaleBorg().format_date_in_string("Foo {month_day_year} Bar", TESLA_BIRTHDAY, lang) == expected_string


@pytest.mark.parametrize("lang, expected_string", [
    (None, 'Foo 10 July 1856 Bar'),
    ('pl', 'Foo 10 lipca 1856 Bar')
], ids=["default", "pl"])
def test_format_date_in_string_month_day_year_gb(lang, expected_string):
    LocaleBorg.initialize({'en': 'en_GB'}, 'en')
    assert LocaleBorg().format_date_in_string("Foo {month_day_year} Bar", TESLA_BIRTHDAY, lang) == expected_string


@pytest.mark.parametrize("message, expected_string", [
    ("Foo {month:'miesiąca' MMMM} Bar", 'Foo miesiąca lipca Bar'),
    ("Foo {month_year:MMMM yyyy} Bar", 'Foo lipca 1856 Bar'),
])
def test_format_date_in_string_customization(base_config, message, expected_string):
    assert LocaleBorg().format_date_in_string(message, TESLA_BIRTHDAY, 'pl') == expected_string


@pytest.mark.parametrize("lang, expected_format", [
    ('sr', '10. јул 1856. 12:34:56 UTC'),
    ('sr_latin', '10. jul 1856. 12:34:56 UTC')
])
def test_locale_base(lang, expected_format):
    LocaleBorg.initialize(LEGAL_VALUES['LOCALES_BASE'], 'en')
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, lang) == expected_format


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
    LocaleBorg.initialize({}, 'en')
