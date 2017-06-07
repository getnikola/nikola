# coding: utf8
# Author: Rodrigo Bistolfi
# Date: 03/2013


""" Base class for Nikola test cases """


__all__ = ["BaseTestCase", "cd", "LocaleSupportInTesting"]


import os
import sys


from contextlib import contextmanager
import locale
import unittest

import logbook

import nikola.utils
import nikola.shortcodes

from yapsy.PluginManager import PluginManager
from nikola.plugin_categories import (
    Command,
    Task,
    LateTask,
    TemplateSystem,
    PageCompiler,
    TaskMultiplier,
    CompilerExtension,
    MarkdownExtension,
    RestExtension
)
nikola.utils.LOGGER.handlers.append(logbook.TestHandler())

BaseTestCase = unittest.TestCase


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)


class LocaleSupportInTesting(object):
    """
    Nikola needs two pairs of valid (language, locale_n) to test multilingual sites.

    As languages of interest and installed OS support varies from host to host
    we allow to specify two such pairs.

    A valid pair complies
        'languaje' one of the names of nikola translations ('en', 'es', ...)
        'locale_n' is a string that python accepts to set a locale, like in
            import locale
            locale.setlocale(locale.LC_ALL, str(locale_n))

    You specify the custom pairs to use with two environment variables
    NIKOLA_LOCALE_DEFAULT (lang and locale to use as nikola's DEFAULT_LANG)
    NIKOLA_LOCALE_OTHER

    The value of the pair is lang (as in keys of Nikola's TRANSLATIONS), followed
    by coma, followed by the locale.
    """

    @classmethod
    def initialize(cls):
        """Determines and diagnoses the two (lang, locale) pairs to use in testing

        While it only needs to run once at the beginning of the testing session,
        calling multiple times is fine.
        """
        if hasattr(cls, 'langlocales'):
            return
        defaults = {
            'posix': {
                # non-windows/non-osx defaults, must be two locales suported by .travis.yml
                'default': ("en", str("en_US.utf8")),
                'other': ("pl", str("pl_PL.utf8")),
            },
            'osx': {
                # osx defaults
                'default': ("en", str("en_US.UTF-8")),
                'other': ("pl", str("pl_PL.UTF-8")),
            },
            'windows': {
                # windows defaults
                'default': ("en", str("English")),
                'other': ("pl", str("Polish")),
            },
        }
        platforms = {
            'win32': 'windows',
            'darwin': 'osx',
        }
        os_id = platforms.get(sys.platform, 'posix')
        langlocales = {}
        for suffix in ['other', 'default']:
            try:
                envar = 'NIKOLA_LOCALE_' + suffix.upper()
                s = os.environ[envar]
                parts = s.split(',')
                lang = parts[0].strip()
                try:
                    locale_n = str(parts[1].strip())
                    locale.setlocale(locale.LC_ALL, locale_n)
                except Exception:
                    msg = ("Environment variable {0} fails to specify a valid <lang>,<locale>." +
                           "Check your syntax, check that python supports that locale in your host.")
                    nikola.utils.LOGGER.error(msg.format(envar))
                    sys.exit(1)
            except KeyError:
                lang, locale_n = defaults[os_id][suffix]
            langlocales[suffix] = (lang, locale_n)
        if (langlocales['default'][0] == langlocales['other'][0] or
            langlocales['default'][1] == langlocales['other'][1]):  # NOQA
            # the mix of defaults and enviro is not good
            msg = ('Locales for testing should differ in lang and locale, else ' +
                   'the test would we weak. Check your environment settings for ' +
                   'NIKOLA_LOCALE_DEFAULT and NIKOLA_LOCALE_OTHER')
            nikola.utils.LOGGER.error(msg)
        setattr(cls, 'langlocales', langlocales)

    @classmethod
    def initialize_locales_for_testing(cls, variant):
        """initializes nikola.utils.LocaleBorg"""
        if not hasattr(cls, 'langlocales'):
            cls.initialize()
        default_lang = cls.langlocales['default'][0]
        locales = {}
        locales[default_lang] = cls.langlocales['default'][1]
        if variant == 'unilingual':
            pass
        elif variant == 'bilingual':
            locales[cls.langlocales['other'][0]] = cls.langlocales['other'][1]
        else:
            raise ValueError('Unknown locale variant')
        nikola.utils.LocaleBorg.reset()
        nikola.utils.LocaleBorg.initialize(locales, default_lang)


class FakePost(object):

    def __init__(self, title, slug):
        self._title = title
        self._slug = slug
        self._meta = {'slug': slug}
        self.default_lang = 'en'
        self._depfile = {}

    def title(self):
        return self._title

    def meta(self, key):
        return self._meta[key]

    def permalink(self):
        return '/posts/' + self._slug


class FakeSite(object):
    def __init__(self):
        self.template_system = self
        self.invariant = False
        self.config = {
            'DISABLED_PLUGINS': [],
            'EXTRA_PLUGINS': [],
            'DEFAULT_LANG': 'en',
            'MARKDOWN_EXTENSIONS': ['markdown.extensions.fenced_code', 'markdown.extensions.codehilite'],
            'TRANSLATIONS_PATTERN': '{path}.{lang}.{ext}',
            'LISTINGS_FOLDERS': {'listings': 'listings'},
        }
        self.EXTRA_PLUGINS = self.config['EXTRA_PLUGINS']
        self.plugin_manager = PluginManager(categories_filter={
            "Command": Command,
            "Task": Task,
            "LateTask": LateTask,
            "TemplateSystem": TemplateSystem,
            "PageCompiler": PageCompiler,
            "TaskMultiplier": TaskMultiplier,
            "CompilerExtension": CompilerExtension,
            "MarkdownExtension": MarkdownExtension,
            "RestExtension": RestExtension
        })
        self.loghandlers = nikola.utils.STDERR_HANDLER  # TODO remove on v8
        self.shortcode_registry = {}
        self.plugin_manager.setPluginInfoExtension('plugin')
        if sys.version_info[0] == 3:
            places = [
                os.path.join(
                    os.path.dirname(nikola.utils.__file__),
                    'plugins'), ]
        else:
            places = [
                os.path.join(
                    os.path.dirname(nikola.utils.__file__),
                    nikola.utils.sys_encode('plugins')), ]
        self.plugin_manager.setPluginPlaces(places)
        self.plugin_manager.collectPlugins()
        self.compiler_extensions = self._activate_plugins_of_category(
            "CompilerExtension")

        self.timeline = [
            FakePost(title='Fake post',
                     slug='fake-post')
        ]
        self.debug = True
        self.rst_transforms = []
        self.post_per_input_file = {}
        # This is to make plugin initialization happy
        self.template_system = self
        self.name = 'mako'

    def _activate_plugins_of_category(self, category):
        """Activate all the plugins of a given category and return them."""
        # this code duplicated in nikola/nikola.py
        plugins = []
        for plugin_info in self.plugin_manager.getPluginsOfCategory(category):
            if plugin_info.name in self.config.get('DISABLED_PLUGINS'):
                self.plugin_manager.removePluginFromCategory(
                    plugin_info, category)
            else:
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)
                plugins.append(plugin_info)
        return plugins

    def render_template(self, name, _, context):
        return('<img src="IMG.jpg">')

    # this code duplicated in nikola/nikola.py
    def register_shortcode(self, name, f):
        """Register function f to handle shortcode "name"."""
        if name in self.shortcode_registry:
            nikola.utils.LOGGER.warn('Shortcode name conflict: %s', name)
            return
        self.shortcode_registry[name] = f

    def apply_shortcodes(self, data, *a, **kw):
        """Apply shortcodes from the registry on data."""
        return nikola.shortcodes.apply_shortcodes(
            data, self.shortcode_registry, **kw)

    def apply_shortcodes_uuid(self, data, shortcodes, *a, **kw):
        """Apply shortcodes from the registry on data."""
        return nikola.shortcodes.apply_shortcodes(
            data, self.shortcode_registry, **kw)
