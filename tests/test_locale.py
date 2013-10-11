# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys

# needed if @unittest.expectedFailure is used
try:
    import unittest2 as unittest
except:
    import unittest

import nikola.nikola

# specified as unicode string because in nikola it will be read from conf.py
# which uses unicode_constants
if sys.platform == 'win32':
    loc_eng = 'English'
    loc_spa = 'Spanish'
else:
    loc_eng = 'en_US.utf8'
    loc_spa = 'es_ES.utf8'

# these are candidates to hardcoded locales, using str() for py2x setlocale
loc_C = str('C')
loc_Cutf8 = str('C.utf8')


class TestHarcodedFallbacks(unittest.TestCase):
    def test_hardcoded_fallbacks_work(self):
        # keep in sync with nikola.valid_locale_fallback
        if sys.platform == 'win32':
            self.assertTrue(nikola.nikola.is_valid_locale(str('English')))
            self.assertTrue(nikola.nikola.is_valid_locale(str('C')))
        else:
            # the 1st is desired in Travis, not a problem if fails in user host
            self.assertTrue(nikola.nikola.is_valid_locale(str('en_US.utf8')))
            # this is supposed to be always true, and we need an universal
            # fallback. Failure is not a problem in user host if he / she
            # sets a valid (in his host) locale_fallback.
            self.assertTrue(nikola.nikola.is_valid_locale(str('C')))


class TestConfigLocale(unittest.TestCase):

    def test_implicit_fallback(self):
        locale_fallback = None
        sanitized_fallback = nikola.nikola.valid_locale_fallback(desired_locale=locale_fallback)
        self.assertTrue(nikola.nikola.is_valid_locale(sanitized_fallback))

    def test_explicit_good_fallback(self):
        locale_fallback = str(loc_spa)
        sanitized_fallback = nikola.nikola.valid_locale_fallback(desired_locale=locale_fallback)
        self.assertEquals(sanitized_fallback, locale_fallback)

    def test_explicit_bad_fallback(self):
        locale_fallback = str('xyz')
        sanitized_fallback = nikola.nikola.valid_locale_fallback(desired_locale=locale_fallback)
        self.assertTrue(nikola.nikola.is_valid_locale(sanitized_fallback))

    def test_explicit_good_default(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_spa,
            loc_eng,
            {},
            {'en': ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertEquals(fallback, locale_fallback)
        self.assertEquals(default, locale_default)

    def test_explicit_bad_default(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_spa,
            str('xyz'),
            {},
            {'en': ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertEquals(fallback, locale_fallback)
        self.assertEquals(default, fallback)

    def test_extra_locales_deleted(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_spa,
            None,
            {'@z': loc_spa},
            {'en': ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertTrue('@z' not in locales)

    def test_explicit_good_locale_retained(self):
        locale_fallback, locale_default, LOCALES, translations = (
            None,
            loc_spa,
            {'en': loc_eng},
            {'en': ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertEquals(locales['en'], str(LOCALES['en']))

    def test_explicit_bad_locale_replaced_with_fallback(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_spa,
            loc_eng,
            {'en': str('xyz')},
            {'en': ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertEquals(locales['en'], locale_fallback)

    def test_impicit_locale_when_default_locale_defined(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_eng,
            loc_spa,
            {},
            {'en': ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertEquals(locales['en'], locale_default)

    def test_impicit_locale_when_default_locale_is_not_defined(self):
        # legacy mode, compat v6.0.4 : guess locale from lang
        locale_fallback, locale_default, LOCALES, translations = (
            loc_spa,
            None,
            {},
            {'en': ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        if sys.platform == 'win32':
            guess_locale_for_lang = nikola.nikola.guess_locale_from_lang_windows
        else:
            guess_locale_for_lang = nikola.nikola.guess_locale_from_lang_linux

        self.assertEquals(locales['en'], guess_locale_for_lang('en'))


class TestCalendarRelated(unittest.TestCase):
    def test_type_of_month_name(self):
        """validate assumption calendar month name is of type str

        Yes, both in windows and linuxTravis, py 26, 27, 33
        """
        import calendar
        if sys.version_info[0] == 3:  # Python 3
            with calendar.different_locale(str(loc_spa)):
                s = calendar.month_name[1]
        else:  # Python 2
            with calendar.TimeEncoding(str(loc_spa)):
                s = calendar.month_name[1]
        self.assertTrue(type(s) == str)


class TestTestPreconditions(unittest.TestCase):
    """if this fails the other test in this module are mostly nonsense
       failure probably means the OS support for the failing locale is not
       instaled.
       To test in a host with other locales, replace both with different,
       existing locales in the host.
    """
    def test_locale_eng_availability(self):
        self.assertTrue(nikola.nikola.is_valid_locale(str(loc_eng)), "META ERROR: locale for english should be valid")

    def test_locale_esp_availability(self):
        self.assertTrue(nikola.nikola.is_valid_locale(str(loc_spa)), "META ERROR: locale for spanish should be valid")
