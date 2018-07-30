# coding: utf8
# Author: Rodrigo Bistolfi
# Date: 03/2013


""" Base class for Nikola test cases """


__all__ = ["BaseTestCase", "cd", "initialize_localeborg", "LOCALE_DEFAULT", "LOCALE_OTHER"]


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

LOCALE_DEFAULT = os.environ.get('NIKOLA_LOCALE_DEFAULT', 'en')
LOCALE_OTHER = os.environ.get('NIKOLA_LOCALE_OTHER', 'pl')


def initialize_localeborg():
    nikola.utils.LocaleBorg.reset()
    nikola.utils.LocaleBorg.initialize({}, LOCALE_DEFAULT)

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
    def initialize_locales_for_testing(cls, variant):
        """initializes nikola.utils.LocaleBorg"""
        nikola.utils.LocaleBorg.reset()
        nikola.utils.LocaleBorg.initialize({}, 'en')

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
        self.debug = True
        self.config = {
            'DISABLED_PLUGINS': [],
            'EXTRA_PLUGINS': [],
            'DEFAULT_LANG': 'en',
            'MARKDOWN_EXTENSIONS': ['markdown.extensions.fenced_code', 'markdown.extensions.codehilite'],
            'TRANSLATIONS_PATTERN': '{path}.{lang}.{ext}',
            'LISTINGS_FOLDERS': {'listings': 'listings'},
            'TRANSLATIONS': {'en': ''},
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
        self.shortcode_registry = {}
        self.plugin_manager.setPluginInfoExtension('plugin')
        places = [os.path.join(os.path.dirname(nikola.utils.__file__), 'plugins')]
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
