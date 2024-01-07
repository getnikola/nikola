"""
Helper utilities and classes for Nikola tests.

Alongside a contextmanager to switch directories this module contains
a Site substitute for rendering tests.
"""

import os
import pathlib
from contextlib import contextmanager

import nikola.shortcodes
import nikola.utils
from nikola.plugin_manager import PluginManager

__all__ = ["cd", "FakeSite"]


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
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
        places = [pathlib.Path(nikola.utils.__file__).parent / "plugins"]
        self.plugin_manager = PluginManager(plugin_places=places)
        self.shortcode_registry = {}
        candidates = self.plugin_manager.locate_plugins()
        self.plugin_manager.load_plugins(candidates)
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
        for plugin_info in self.plugin_manager.get_plugins_of_category(category):
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
