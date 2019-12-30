"""
Helper utilities and classes for Nikola tests.

Alongside a contextmanager to switch directories this module contains
a Site substitute for rendering tests.
"""

import os
from contextlib import contextmanager

from yapsy.PluginManager import PluginManager

import nikola.utils
import nikola.shortcodes
from nikola.plugin_categories import (
    Command,
    Task,
    LateTask,
    TemplateSystem,
    PageCompiler,
    TaskMultiplier,
    CompilerExtension,
    MarkdownExtension,
    RestExtension,
)

__all__ = ["cd", "FakeSite"]


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)


class FakeSite:
    def __init__(self):
        self.template_system = self
        self.invariant = False
        self.debug = True
        self.config = {
            "DISABLED_PLUGINS": [],
            "EXTRA_PLUGINS": [],
            "DEFAULT_LANG": "en",
            "MARKDOWN_EXTENSIONS": [
                "markdown.extensions.fenced_code",
                "markdown.extensions.codehilite",
            ],
            "TRANSLATIONS_PATTERN": "{path}.{lang}.{ext}",
            "LISTINGS_FOLDERS": {"listings": "listings"},
            "TRANSLATIONS": {"en": ""},
        }
        self.EXTRA_PLUGINS = self.config["EXTRA_PLUGINS"]
        self.plugin_manager = PluginManager(
            categories_filter={
                "Command": Command,
                "Task": Task,
                "LateTask": LateTask,
                "TemplateSystem": TemplateSystem,
                "PageCompiler": PageCompiler,
                "TaskMultiplier": TaskMultiplier,
                "CompilerExtension": CompilerExtension,
                "MarkdownExtension": MarkdownExtension,
                "RestExtension": RestExtension,
            }
        )
        self.shortcode_registry = {}
        self.plugin_manager.setPluginInfoExtension("plugin")
        places = [os.path.join(os.path.dirname(nikola.utils.__file__), "plugins")]
        self.plugin_manager.setPluginPlaces(places)
        self.plugin_manager.collectPlugins()
        self.compiler_extensions = self._activate_plugins_of_category(
            "CompilerExtension"
        )

        self.timeline = [FakePost(title="Fake post", slug="fake-post")]
        self.rst_transforms = []
        self.post_per_input_file = {}
        # This is to make plugin initialization happy
        self.template_system = self
        self.name = "mako"

    def _activate_plugins_of_category(self, category):
        """Activate all the plugins of a given category and return them."""
        # this code duplicated in nikola/nikola.py
        plugins = []
        for plugin_info in self.plugin_manager.getPluginsOfCategory(category):
            if plugin_info.name in self.config.get("DISABLED_PLUGINS"):
                self.plugin_manager.removePluginFromCategory(plugin_info, category)
            else:
                self.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self)
                plugins.append(plugin_info)
        return plugins

    def render_template(self, name, _, context):
        return '<img src="IMG.jpg">'

    # this code duplicated in nikola/nikola.py
    def register_shortcode(self, name, f):
        """Register function f to handle shortcode "name"."""
        if name in self.shortcode_registry:
            nikola.utils.LOGGER.warning('Shortcode name conflict: %s', name)
            return
        self.shortcode_registry[name] = f

    def apply_shortcodes(self, data, *a, **kw):
        """Apply shortcodes from the registry on data."""
        return nikola.shortcodes.apply_shortcodes(data, self.shortcode_registry, **kw)

    def apply_shortcodes_uuid(self, data, shortcodes, *a, **kw):
        """Apply shortcodes from the registry on data."""
        return nikola.shortcodes.apply_shortcodes(data, self.shortcode_registry, **kw)


class FakePost:
    def __init__(self, title, slug):
        self._title = title
        self._slug = slug
        self._meta = {"slug": slug}

    def title(self):
        return self._title

    def meta(self, key):
        return self._meta[key]

    def permalink(self):
        return "/posts/" + self._slug
