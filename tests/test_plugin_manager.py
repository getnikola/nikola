# -*- coding: utf-8 -*-

# Copyright © 2012-2025 Chris Warrick and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import nikola.plugin_manager

from .helper import FakeSite
from nikola.plugin_manager import PluginManager
from pathlib import Path


def test_locate_plugins_finds_core_plugins():
    """Ensure that locate_plugins can find some core plugins."""
    places = [Path(nikola.plugin_manager.__file__).parent / "plugins"]
    plugin_manager = PluginManager(places)
    candidates = plugin_manager.locate_plugins()
    plugin_names = [p.name for p in candidates]
    assert plugin_manager.candidates == candidates

    assert "emoji" in plugin_names
    assert "copy_assets" in plugin_names
    assert "scan_posts" in plugin_names

    template_plugins = [p for p in candidates if p.category == "TemplateSystem"]
    template_plugins.sort(key=lambda p: p.name)
    assert len(template_plugins) == 2
    assert template_plugins[0].name == "jinja"
    assert template_plugins[1].name == "mako"


def test_locate_plugins_finds_core_and_custom_plugins():
    """Ensure that locate_plugins can find some custom plugins."""
    places = [
        Path(nikola.plugin_manager.__file__).parent / "plugins",
        Path(__file__).parent / "data" / "plugin_manager",
    ]
    plugin_manager = PluginManager(places)
    candidates = plugin_manager.locate_plugins()
    plugin_names = [p.name for p in candidates]
    assert plugin_manager.candidates == candidates

    assert "emoji" in plugin_names
    assert "copy_assets" in plugin_names
    assert "scan_posts" in plugin_names

    assert "first" in plugin_names
    assert "2nd" in plugin_names

    first_plugin = next(p for p in candidates if p.name == "first")
    second_plugin = next(p for p in candidates if p.name == "2nd")

    assert first_plugin.category == "Command"
    assert first_plugin.compiler == "foo"
    assert first_plugin.source_dir == places[1]

    assert second_plugin.category == "ConfigPlugin"
    assert second_plugin.compiler is None
    assert second_plugin.source_dir == places[1] / "second"


def test_load_plugins():
    """Ensure that locate_plugins can load some core and custom plugins."""
    places = [
        Path(nikola.plugin_manager.__file__).parent / "plugins",
        Path(__file__).parent / "data" / "plugin_manager",
    ]
    plugin_manager = PluginManager(places)
    candidates = plugin_manager.locate_plugins()
    plugins_to_load = [p for p in candidates if p.name in {"first", "2nd", "emoji"}]

    plugin_manager.load_plugins(plugins_to_load)

    assert len(plugin_manager.plugins) == 3
    assert plugin_manager._plugins_by_category["ShortcodePlugin"][0].name == "emoji"
    assert plugin_manager._plugins_by_category["Command"][0].name == "first"
    assert plugin_manager._plugins_by_category["ConfigPlugin"][0].name == "2nd"

    site = FakeSite()
    for plugin in plugin_manager.plugins:
        plugin.plugin_object.set_site(site)

    assert "emoji" in site.shortcode_registry
    assert plugin_manager.get_plugin_by_name("first", "Command").plugin_object.one_site_set
    assert plugin_manager.get_plugin_by_name("2nd").plugin_object.two_site_set
    assert plugin_manager.get_plugin_by_name("2nd", "Command") is None


def test_load_plugins_twice():
    """Ensure that extra plugins can be added."""
    places = [
        Path(nikola.plugin_manager.__file__).parent / "plugins",
        Path(__file__).parent / "data" / "plugin_manager",
    ]
    plugin_manager = PluginManager(places)
    candidates = plugin_manager.locate_plugins()
    plugins_to_load_first = [p for p in candidates if p.name in {"first", "emoji"}]
    plugins_to_load_second = [p for p in candidates if p.name in {"2nd"}]

    plugin_manager.load_plugins(plugins_to_load_first)
    assert len(plugin_manager.plugins) == 2
    plugin_manager.load_plugins(plugins_to_load_second)
    assert len(plugin_manager.plugins) == 3


def test_load_plugins_skip_mismatching_category(caplog):
    """If a plugin specifies a different category than it actually implements, refuse to load it."""
    places = [
        Path(__file__).parent / "data" / "plugin_manager",
    ]
    plugin_manager = PluginManager(places)
    candidates = plugin_manager.locate_plugins()
    plugins_to_load = [p for p in candidates if p.name in {"broken"}]
    plugin_to_load = plugins_to_load[0]
    assert len(plugins_to_load) == 1

    plugin_manager.load_plugins(plugins_to_load)

    py_file = plugin_to_load.source_dir / "broken.py"
    assert f"{plugin_to_load.plugin_id} ({py_file}) has category '{plugin_to_load.category}' in the .plugin file, but the implementation class <class 'tests.data.plugin_manager.broken.BrokenPlugin'> does not inherit from this category - plugin will not be loaded" in caplog.text
    assert len(plugin_manager.plugins) == 0
