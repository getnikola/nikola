# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys


# needed if @unittest.expectedFailure is used
try:
    import unittest2 as unittest
except:
    import unittest

import nikola.nikola
import nikola.utils
from .base import LocaleSupportInTesting

LocaleSupportInTesting.initialize_locales_for_testing('bilingual')
lang_11, loc_11 = LocaleSupportInTesting.langlocales['default']
lang_22, loc_22 = LocaleSupportInTesting.langlocales['other']


# these are candidates to hardcoded locales, using str() for py2x setlocale
loc_C = str('C')
loc_Cutf8 = str('C.utf8')

if sys.platform != 'win32':
    nikola.nikola.workaround_empty_LC_ALL_posix()


class TestHarcodedFallbacks(unittest.TestCase):
    def test_hardcoded_fallbacks_work(self):
        # keep in sync with nikola.valid_locale_fallback
        if sys.platform == 'win32':
            self.assertTrue(nikola.nikola.is_valid_locale(str('English')))
            self.assertTrue(nikola.nikola.is_valid_locale(str('C')))
        else:
            # the 1st is desired in Travis, not a problem if fails in user host
            self.assertTrue(nikola.nikola.is_valid_locale(str('en_US.utf8')))
            # this is supposed to be always valid, and we need an universal
            # fallback. Failure is not a problem in user host if he / she
            # sets a valid (in his host) locale_fallback.
            self.assertTrue(nikola.nikola.is_valid_locale(str('C')))


class TestConfigLocale(unittest.TestCase):

    def test_implicit_fallback(self):
        locale_fallback = None
        sanitized_fallback = nikola.nikola.valid_locale_fallback(
            desired_locale=locale_fallback)
        self.assertTrue(nikola.nikola.is_valid_locale(sanitized_fallback))

    def test_explicit_good_fallback(self):
        locale_fallback = loc_22
        sanitized_fallback = nikola.nikola.valid_locale_fallback(
            desired_locale=locale_fallback)
        self.assertEquals(sanitized_fallback, locale_fallback)

    def test_explicit_bad_fallback(self):
        locale_fallback = str('xyz')
        sanitized_fallback = nikola.nikola.valid_locale_fallback(
            desired_locale=locale_fallback)
        self.assertTrue(nikola.nikola.is_valid_locale(sanitized_fallback))

    def test_explicit_good_default(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_22,
            loc_11,
            {},
            {lang_11: ''},
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
            loc_22,
            str('xyz'),
            {},
            {lang_11: ''},
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
            loc_22,
            None,
            {'@z': loc_22},
            {lang_11: ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertTrue('@z' not in locales)

    def test_explicit_good_locale_retained(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_22,
            loc_22,
            {lang_11: loc_11},
            {lang_11: ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertEquals(locales[lang_11], str(LOCALES[lang_11]))

    def test_explicit_bad_locale_replaced_with_fallback(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_22,
            loc_11,
            {lang_11: str('xyz')},
            {lang_11: ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        self.assertEquals(locales['en'], locale_fallback)

    def test_impicit_locale_when_default_locale_defined(self):
        locale_fallback, locale_default, LOCALES, translations = (
            loc_11,
            loc_22,
            {},
            {lang_11: ''},
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
            loc_22,
            None,
            {},
            {lang_11: ''},
        )
        fallback, default, locales = nikola.nikola.sanitized_locales(
            locale_fallback,
            locale_default,
            LOCALES,
            translations)
        if sys.platform == 'win32':
            guess_locale_for_lang = nikola.nikola.guess_locale_from_lang_windows
        else:
            guess_locale_for_lang = nikola.nikola.guess_locale_from_lang_posix

        self.assertEquals(locales[lang_11], guess_locale_for_lang(lang_11))


class TestCalendarRelated(unittest.TestCase):
    def test_type_of_month_name(self):
        """validate assumption calendar month name is of type str

        Yes, both in windows and linuxTravis, py 26, 27, 33
        """
        import calendar
        if sys.version_info[0] == 3:  # Python 3
            with calendar.different_locale(loc_11):
                s = calendar.month_name[1]
        else:  # Python 2
            with calendar.TimeEncoding(loc_11):
                s = calendar.month_name[1]
        self.assertTrue(type(s) == str)


class TestLocaleBorg(unittest.TestCase):
    def test_initial_lang(self):
        lang_11, loc_11 = LocaleSupportInTesting.langlocales['default']
        lang_22, loc_22 = LocaleSupportInTesting.langlocales['other']

        locales = {lang_11: loc_11, lang_22: loc_22}
        initial_lang = lang_22
        nikola.utils.LocaleBorg.initialize(locales, initial_lang)
        self.assertEquals(initial_lang, nikola.utils.LocaleBorg().current_lang)

    def test_remembers_last_lang(self):
        lang_11, loc_11 = LocaleSupportInTesting.langlocales['default']
        lang_22, loc_22 = LocaleSupportInTesting.langlocales['other']

        locales = {lang_11: loc_11, lang_22: loc_22}
        initial_lang = lang_22
        nikola.utils.LocaleBorg.initialize(locales, initial_lang)

        nikola.utils.LocaleBorg().set_locale(lang_11)
        self.assertTrue(nikola.utils.LocaleBorg().current_lang, lang_11)

    def test_services_ensure_initialization(self):
        nikola.utils.LocaleBorg.reset()
        self.assertRaises(Exception, nikola.utils.LocaleBorg)

    def test_services_reject_dumb_wrong_call(self):
        lang_11, loc_11 = LocaleSupportInTesting.langlocales['default']
        nikola.utils.LocaleBorg.reset()
        self.assertRaises(Exception, nikola.utils.LocaleBorg)
        self.assertRaises(Exception, nikola.utils.LocaleBorg.set_locale, lang_11)

    def test_set_locale_raises_on_invalid_lang(self):
        lang_11, loc_11 = LocaleSupportInTesting.langlocales['default']
        lang_22, loc_22 = LocaleSupportInTesting.langlocales['other']

        locales = {lang_11: loc_11, lang_22: loc_22}
        initial_lang = lang_22
        nikola.utils.LocaleBorg.initialize(locales, initial_lang)
        self.assertRaises(KeyError, nikola.utils.LocaleBorg().set_locale, '@z')


class TestTestPreconditions(unittest.TestCase):
    """If this fails the other test in this module are mostly nonsense, and
       probably same for tests of multilingual features.

       Failure probably means the OS support for the failing locale is not
       instaled or environmet variables NIKOLA_LOCALE_DEFAULT  or
       NIKOLA_LOCALE_OTHER with bad values.
    """
    def test_langlocale_default_availability(self):
        msg = "META ERROR: The pair lang, locale : {0} {1} is invalid"
        self.assertTrue(nikola.nikola.is_valid_locale(loc_11), msg.format(lang_11, loc_11))

    def test_langlocale_other_availability(self):
        msg = "META ERROR: The pair lang, locale : {0} {1} is invalid"
        self.assertTrue(nikola.nikola.is_valid_locale(loc_22), msg.format(lang_22, loc_22))
