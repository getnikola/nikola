# -*- coding: utf-8 -*-

import datetime
import dateutil
import pytest
import unittest.mock
from nikola.nikola import LEGAL_VALUES
from nikola.utils import TranslatableSetting, LocaleBorg, LocaleBorgUninitializedException

TESLA_BIRTHDAY = datetime.date(1856, 7, 10)
TESLA_BIRTHDAY_DT = datetime.datetime(1856, 7, 10, 12, 34, 56)
DT_EN_US = 'July 10, 1856 at 12:34:56 PM UTC'

DT_PL = '10 lipca 1856 12:34:56 UTC'


@pytest.fixture
def localeborg_base():
    """A base config of LocaleBorg."""
    LocaleBorg.reset()
    assert not LocaleBorg.initialized
    LocaleBorg.initialize({}, 'en')
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == 'en'
    return None


def test_initilalize_failure():
    LocaleBorg.reset()
    with pytest.raises(ValueError):
        LocaleBorg.initialize({}, None)
        LocaleBorg.initialize({}, '')
    assert not LocaleBorg.initialized


def test_initialize():
    LocaleBorg.reset()
    assert not LocaleBorg.initialized
    LocaleBorg.initialize({}, 'en')
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == 'en'
    LocaleBorg.reset()
    LocaleBorg.initialize({}, 'pl')
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == 'pl'


def test_uninitialized_error():
    LocaleBorg.reset()
    with pytest.raises(LocaleBorgUninitializedException):
        LocaleBorg()


def test_set_locale(localeborg_base):
    LocaleBorg().set_locale('pl')
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == 'pl'
    LocaleBorg().set_locale('xx')  # fake language -- used to ensure any locale can be supported
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == 'xx'
    assert LocaleBorg().set_locale('xz') == ''  # empty string for template ease of use


def test_format_date_webiso_basic(localeborg_base):
    with unittest.mock.patch('babel.dates.format_datetime') as m:
        assert LocaleBorg().formatted_date('webiso', TESLA_BIRTHDAY_DT) == '1856-07-10T12:34:56'
        m.assert_not_called()


def test_format_date_basic(localeborg_base):
    assert LocaleBorg().formatted_date('YYYY-MM-dd HH:mm:ss', TESLA_BIRTHDAY_DT) == '1856-07-10 12:34:56'
    LocaleBorg().set_locale('pl')
    assert LocaleBorg().formatted_date('YYYY-MM-dd HH:mm:ss', TESLA_BIRTHDAY_DT) == '1856-07-10 12:34:56'


def test_format_date_long(localeborg_base):
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT) == DT_EN_US
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'en') == DT_EN_US
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'pl') == DT_PL
    LocaleBorg().set_locale('pl')
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT) == DT_PL
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'en') == DT_EN_US


def test_format_date_timezone(localeborg_base):
    tesla_birthday_dtz = datetime.datetime(1856, 7, 10, 12, 34, 56, tzinfo=dateutil.tz.gettz('America/New_York'))
    assert LocaleBorg().formatted_date('long', tesla_birthday_dtz) == 'July 10, 1856 at 12:34:56 PM -0400'


def test_format_date_locale_variants():
    LocaleBorg.reset()
    LocaleBorg.initialize({'en': 'en_US'}, 'en')
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'en') == DT_EN_US
    LocaleBorg.reset()
    LocaleBorg.initialize({'en': 'en_GB'}, 'en')
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'en') == '10 July 1856 at 12:34:56 UTC'


def test_format_date_translatablesetting(localeborg_base):
    df = TranslatableSetting("DATE_FORMAT", {'en': "'en' MMMM", 'pl': "MMMM 'pl'"}, {'en': '', 'pl': ''})
    assert LocaleBorg().formatted_date(df, TESLA_BIRTHDAY_DT, 'en') == 'en July'
    assert LocaleBorg().formatted_date(df, TESLA_BIRTHDAY_DT, 'pl') == 'lipca pl'


def test_format_date_in_string_month(localeborg_base):
    assert LocaleBorg().format_date_in_string("Foo {month} Bar", TESLA_BIRTHDAY) == 'Foo July Bar'
    assert LocaleBorg().format_date_in_string("Foo {month} Bar", TESLA_BIRTHDAY, 'pl') == 'Foo lipiec Bar'


def test_format_date_in_string_month_year(localeborg_base):
    assert LocaleBorg().format_date_in_string("Foo {month_year} Bar", TESLA_BIRTHDAY) == 'Foo July 1856 Bar'
    assert LocaleBorg().format_date_in_string("Foo {month_year} Bar", TESLA_BIRTHDAY, 'pl') == 'Foo lipiec 1856 Bar'


def test_format_date_in_string_month_day_year(localeborg_base):
    assert LocaleBorg().format_date_in_string("Foo {month_day_year} Bar", TESLA_BIRTHDAY) == 'Foo July 10, 1856 Bar'
    assert LocaleBorg().format_date_in_string("Foo {month_day_year} Bar", TESLA_BIRTHDAY,
                                              'pl') == 'Foo 10 lipca 1856 Bar'


def test_format_date_in_string_month_day_year_gb():
    LocaleBorg.reset()
    LocaleBorg.initialize({'en': 'en_GB'}, 'en')
    assert LocaleBorg().format_date_in_string("Foo {month_day_year} Bar", TESLA_BIRTHDAY) == 'Foo 10 July 1856 Bar'
    assert LocaleBorg().format_date_in_string("Foo {month_day_year} Bar", TESLA_BIRTHDAY,
                                              'pl') == 'Foo 10 lipca 1856 Bar'


def test_format_date_in_string_customization(localeborg_base):
    assert LocaleBorg().format_date_in_string("Foo {month:'miesiąca' MMMM} Bar", TESLA_BIRTHDAY,
                                              'pl') == 'Foo miesiąca lipca Bar'
    assert LocaleBorg().format_date_in_string("Foo {month_year:MMMM yyyy} Bar", TESLA_BIRTHDAY,
                                              'pl') == 'Foo lipca 1856 Bar'


def test_locale_base():
    LocaleBorg.reset()
    LocaleBorg.initialize(LEGAL_VALUES['LOCALES_BASE'], 'en')
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'sr') == '10. јул 1856. 12:34:56 UTC'
    assert LocaleBorg().formatted_date('long', TESLA_BIRTHDAY_DT, 'sr_latin') == '10. jul 1856. 12:34:56 UTC'
