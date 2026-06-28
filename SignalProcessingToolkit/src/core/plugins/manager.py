from __future__ import annotations

import inspect
import logging
from importlib import util as importlib_util
from pathlib import Path
from typing import Any

from src.config import settings
from src.core.exceptions import PluginError
from src.core.plugins.interface import PluginMetadata, SignalPlugin
from src.models.signal import Signal

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, SignalPlugin] = {}
        self._plugin_dirs: list[Path] = [settings.plugins_dir]

    def discover(self, extra_dirs: list[Path] | None = None) -> list[PluginMetadata]:
        discovered: list[PluginMetadata] = []
        search_dirs = self._plugin_dirs + (extra_dirs or [])

        for plugin_dir in search_dirs:
            if not plugin_dir.exists():
                continue
            for py_file in plugin_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                try:
                    spec = importlib_util.spec_from_file_location(py_file.stem, str(py_file))
                    if spec is None or spec.loader is None:
                        continue
                    module = importlib_util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for _name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, SignalPlugin) and obj is not SignalPlugin:
                            instance: SignalPlugin = obj()
                            meta = instance.get_metadata()
                            self._plugins[meta.name] = instance
                            discovered.append(meta)
                            logger.info("Discovered plugin: %s v%s", meta.name, meta.version)
                except Exception as e:
                    logger.warning("Failed to load plugin %s: %s", py_file.name, e)

        return discovered

    def get_plugin(self, name: str) -> SignalPlugin | None:
        return self._plugins.get(name)

    def get_all_plugins(self) -> dict[str, SignalPlugin]:
        return dict(self._plugins)

    def process(self, plugin_name: str, signal: Signal, **params: Any) -> Signal:
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            raise PluginError(f"Plugin not found: {plugin_name}")
        return plugin.process(signal, **params)

    def cleanup_all(self) -> None:
        for name, plugin in self._plugins.items():
            try:
                plugin.cleanup()
                logger.debug("Cleaned up plugin: %s", name)
            except Exception as e:
                logger.error("Plugin cleanup failed %s: %s", name, e)
        self._plugins.clear()
