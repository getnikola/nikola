# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Chris Warrick and others.

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

"""The Nikola plugin manager. Inspired by yapsy."""

import configparser
import importlib
import importlib.util
import time
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Type, TYPE_CHECKING, Set

from .plugin_categories import BasePlugin, CATEGORIES
from .utils import get_logger

if TYPE_CHECKING:
    import logging

LEGACY_PLUGIN_NAMES: Dict[str, str] = {
    "Compiler": "PageCompiler",
    "Shortcode": "ShortcodePlugin",
    "Template": "TemplateSystem",
}

CATEGORY_NAMES: Set[str] = set(CATEGORIES.keys())
CATEGORY_TYPES: Set[Type[BasePlugin]] = set(CATEGORIES.values())


@dataclass(frozen=True)
class PluginCandidate:
    """A candidate plugin that was located but not yet loaded (imported)."""

    name: str
    description: Optional[str]
    plugin_id: str
    category: str
    compiler: Optional[str]
    source_dir: Path
    module_name: str


@dataclass(frozen=True)
class PluginInfo:
    """A plugin that was loaded (imported)."""

    name: str
    description: Optional[str]
    plugin_id: str
    category: str
    compiler: Optional[str]
    source_dir: Path
    module_name: str
    module_object: object
    plugin_object: BasePlugin


class PluginManager:
    """The Nikola plugin manager."""

    categories_filter: Dict[str, Type[BasePlugin]]
    plugin_places: List[Path]
    logger: "logging.Logger"
    candidates: List[PluginCandidate]
    plugins: List[PluginInfo]
    _plugins_by_category: Dict[str, List[PluginInfo]]
    has_warnings: bool = False

    def __init__(self, plugin_places: List[Path]):
        """Initialize the plugin manager."""
        self.plugin_places = plugin_places
        self.candidates = []
        self.plugins = []
        self._plugins_by_category = {}
        self.logger = get_logger("PluginManager")

    def locate_plugins(self) -> List[PluginCandidate]:
        """Locate plugins in plugin_places."""
        self.candidates = []

        plugin_files: List[Path] = []
        for place in self.plugin_places:
            plugin_files += place.rglob("*.plugin")

        for plugin_file in plugin_files:
            source_dir = plugin_file.parent
            config = configparser.ConfigParser()
            config.read(plugin_file)
            name = config["Core"]["name"]
            module_name = config["Core"]["module"]
            plugin_id = f"Plugin {name} from {plugin_file}"
            description = None
            if "Documentation" in config:
                description = config["Documentation"].get("Description")
            if "Nikola" not in config:
                self.logger.warning(f"{plugin_id} does not specify Nikola configuration - plugin will not be loaded")
                self.logger.warning("Please add a [Nikola] section to the {plugin_file} file with a PluginCategory entry")
                self.has_warnings = True
                continue
            category = config["Nikola"].get("PluginCategory")
            compiler = config["Nikola"].get("Compiler")
            if not category:
                self.logger.warning(f"{plugin_id} does not specify any category (Nikola.PluginCategory is missing in .plugin file) - plugin will not be loaded")
                self.has_warnings = True
                continue
            if category in LEGACY_PLUGIN_NAMES:
                category = LEGACY_PLUGIN_NAMES[category]
            if category not in CATEGORY_NAMES:
                self.logger.warning(f"{plugin_id} specifies invalid category '{category}' in the .plugin file - plugin will not be loaded")
                self.has_warnings = True
                continue
            self.logger.debug(f"Discovered {plugin_id}")
            self.candidates.append(
                PluginCandidate(
                    name=name,
                    description=description,
                    plugin_id=plugin_id,
                    category=category,
                    compiler=compiler,
                    source_dir=source_dir,
                    module_name=module_name,
                )
            )
        return self.candidates

    def load_plugins(self, candidates: List[PluginCandidate]) -> None:
        """Load selected candidate plugins."""
        plugins_root = Path(__file__).parent.parent

        for candidate in candidates:
            name = candidate.name
            module_name = candidate.module_name
            source_dir = candidate.source_dir
            py_file_location = source_dir / f"{module_name}.py"
            plugin_id = candidate.plugin_id
            if not py_file_location.exists():
                py_file_location = source_dir / module_name / "__init__.py"
            if not py_file_location.exists():
                self.logger.warning(f"{plugin_id} could not be loaded (no valid module detected)")
                self.has_warnings = True
                continue

            plugin_id += f" ({py_file_location})"
            full_module_name = module_name

            try:
                name_parts = list(py_file_location.relative_to(plugins_root).parts)
                if name_parts[-1] == "__init__.py":
                    name_parts.pop(-1)
                elif name_parts[-1].endswith(".py"):
                    name_parts[-1] = name_parts[-1][:-3]
                full_module_name = ".".join(name_parts)
            except ValueError:
                pass

            try:
                spec = importlib.util.spec_from_file_location(full_module_name, py_file_location)
                module_object = importlib.util.module_from_spec(spec)
                if full_module_name not in sys.modules:
                    sys.modules[full_module_name] = module_object
                spec.loader.exec_module(module_object)
            except Exception:
                self.logger.exception(f"{plugin_id} threw an exception while loading")
                self.has_warnings = True
                continue

            plugin_classes = [
                c
                for c in vars(module_object).values()
                if isinstance(c, type) and issubclass(c, BasePlugin) and c not in CATEGORY_TYPES
            ]
            if len(plugin_classes) == 0:
                self.logger.warning(f"{plugin_id} does not have any plugin classes - plugin will not be loaded")
                self.has_warnings = True
                continue
            elif len(plugin_classes) > 1:
                self.logger.warning(f"{plugin_id} has multiple plugin classes; this is not supported - plugin will not be loaded")
                self.has_warnings = True
                continue

            plugin_class = plugin_classes[0]

            if not issubclass(plugin_class, CATEGORIES[candidate.category]):
                self.logger.warning(f"{plugin_id} has category '{candidate.category}' in the .plugin file, but the implementation class {plugin_class} does not inherit from this category - plugin will not be loaded")
                self.has_warnings = True
                continue

            try:
                plugin_object = plugin_class()
            except Exception:
                self.logger.exception(f"{plugin_id} threw an exception while creating the instance")
                self.has_warnings = True
                continue
            self.logger.debug(f"Loaded {plugin_id}")
            info = PluginInfo(
                name=name,
                description=candidate.description,
                plugin_id=candidate.plugin_id,
                category=candidate.category,
                compiler=candidate.compiler,
                source_dir=source_dir,
                module_name=module_name,
                module_object=module_object,
                plugin_object=plugin_object,
            )
            self.plugins.append(info)

        self._plugins_by_category = {category: [] for category in CATEGORY_NAMES}
        for plugin_info in self.plugins:
            self._plugins_by_category[plugin_info.category].append(plugin_info)

        if self.has_warnings:
            self.logger.warning("Some plugins failed to load. Please review the above warning messages.")
            # TODO remove following messages and delay in v8.3.1
            self.logger.warning("You may need to update some plugins (from plugins.getnikola.com) or to fix their .plugin files.")
            self.logger.warning("Waiting 2 seconds before continuing.")
            time.sleep(2)

    def get_plugins_of_category(self, category: str) -> List[PluginInfo]:
        """Get loaded plugins of a given category."""
        return self._plugins_by_category.get(category, [])

    def get_plugin_by_name(self, name: str, category: Optional[str] = None) -> Optional[PluginInfo]:
        """Get a loaded plugin by name and optionally by category. Returns None if no such plugin is loaded."""
        for p in self.plugins:
            if p.name == name and (category is None or p.category == category):
                return p

    # Aliases for Yapsy compatibility
    # TODO: remove in v9
    def getPluginsOfCategory(self, category: str) -> List[PluginInfo]:
        """Get loaded plugins of a given category."""
        self.logger.warning("Legacy getPluginsOfCategory method was used, it may be removed in the future. Please change it to get_plugins_of_category.")
        return self._plugins_by_category.get(category, [])

    # TODO: remove in v9
    def getPluginByName(self, name: str, category: Optional[str] = None) -> Optional[PluginInfo]:
        """Get a loaded plugin by name and optionally by category. Returns None if no such plugin is loaded."""
        self.logger.warning("Legacy getPluginByName method was used, it may be removed in the future. Please change it to get_plugin_by_name.")
        return self.get_plugin_by_name(name, category)
