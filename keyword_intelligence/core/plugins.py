"""Plugin System for dynamic discovery and lifecycle management."""

from __future__ import annotations

import importlib.metadata
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

from keyword_intelligence.core.exceptions import InitializationError


class PluginLifecycle(ABC):
    """Lifecycle interface that all plugins must implement."""

    @abstractmethod
    def initialize(self) -> None:
        """Called immediately after instantiation."""
        pass

    @abstractmethod
    def register(self) -> None:
        """Register components with the central IoC container."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start any background tasks or connections."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Gracefully shut down plugin resources."""
        pass

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Return diagnostic health info for this plugin.

        Returns:
            Dictionary containing at least {"status": "healthy" | "unhealthy"}
        """
        pass


class PluginLoader(ABC):
    """Strategy interface for discovering and loading plugins."""

    @abstractmethod
    def load(self) -> list[PluginLifecycle]:
        """Discover, instantiate, and return plugins."""
        pass


class EntryPointPluginLoader(PluginLoader):
    """Discovers plugins via importlib.metadata entry points."""

    def __init__(self, group_name: str = "keyword_intelligence.plugins") -> None:
        self.group_name = group_name

    def load(self) -> list[PluginLifecycle]:
        plugins = []
        try:
            entry_points = importlib.metadata.entry_points(group=self.group_name)
        except TypeError:
            # Fallback for older Python versions
            eps = importlib.metadata.entry_points()
            entry_points = eps.get(self.group_name, [])  # type: ignore

        for ep in entry_points:
            try:
                plugin_cls = ep.load()
                if issubclass(plugin_cls, PluginLifecycle):
                    plugins.append(plugin_cls())
                    logger.debug(f"Loaded plugin from entry point: {ep.name}")
                else:
                    logger.warning(
                        f"Entry point {ep.name} does not implement PluginLifecycle."
                    )
            except Exception as e:
                logger.error(f"Failed to load entry point plugin {ep.name}: {e}")
        return plugins


class LocalDirectoryPluginLoader(PluginLoader):
    """Discovers plugins from a local directory (for dev/demo)."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def load(self) -> list[PluginLifecycle]:
        plugins = []
        if not self.directory.exists() or not self.directory.is_dir():
            return plugins

        for py_file in self.directory.rglob("*.py"):
            if py_file.name == "__init__.py" or py_file.name.startswith("."):
                continue

            module_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Scan for PluginLifecycle subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, PluginLifecycle)
                            and attr is not PluginLifecycle
                        ):
                            plugins.append(attr())
                            logger.debug(f"Loaded plugin from local file: {py_file}")
            except Exception as e:
                logger.error(f"Failed to load local plugin {py_file}: {e}")

        return plugins


class ManualPluginLoader(PluginLoader):
    """Loads a pre-defined list of plugins (useful for testing)."""

    def __init__(self, plugins: list[PluginLifecycle]) -> None:
        self._plugins = plugins

    def load(self) -> list[PluginLifecycle]:
        return self._plugins


class PluginManager:
    """Manages discovery, registration, and lifecycle of all plugins."""

    def __init__(self) -> None:
        self._loaders: list[PluginLoader] = []
        self._plugins: list[PluginLifecycle] = []

    def add_loader(self, loader: PluginLoader) -> None:
        """Add a discovery mechanism."""
        self._loaders.append(loader)

    def load_all(self) -> None:
        """Execute all loaders and initialize plugins."""
        for loader in self._loaders:
            discovered = loader.load()
            for plugin in discovered:
                try:
                    plugin.initialize()
                    self._plugins.append(plugin)
                except Exception as e:
                    logger.error(
                        f"Plugin {plugin.__class__.__name__} failed to initialize: {e}"
                    )

    def register_all(self) -> None:
        """Register all plugins with the IoC container."""
        for plugin in self._plugins:
            try:
                plugin.register()
            except Exception as e:
                logger.error(
                    f"Plugin {plugin.__class__.__name__} failed to register: {e}"
                )

    def start_all(self) -> None:
        """Start all plugins."""
        for plugin in self._plugins:
            try:
                plugin.start()
            except Exception as e:
                raise InitializationError(
                    f"Plugin {plugin.__class__.__name__} failed to start: {e}"
                )

    def stop_all(self) -> None:
        """Stop all plugins."""
        for plugin in reversed(self._plugins):
            try:
                plugin.stop()
            except Exception as e:
                logger.error(f"Plugin {plugin.__class__.__name__} failed to stop: {e}")

    def health_report(self) -> dict[str, Any]:
        """Aggregate health checks from all plugins."""
        report: dict[str, Any] = {}
        for plugin in self._plugins:
            name = plugin.__class__.__name__
            try:
                report[name] = plugin.health_check()
            except Exception as e:
                report[name] = {"status": "unhealthy", "error": str(e)}
        return report
