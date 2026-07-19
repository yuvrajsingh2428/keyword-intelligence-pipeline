# Plugin Author Guide

The Pipeline supports auto-discovery of third-party plugins.

## Creating a Plugin

1. Create a class that implements `keyword_intelligence.core.plugins.PluginLifecycle`.
2. Implement `initialize`, `register`, `start`, `stop`, and `health_check`.
3. Inside `register`, use `container.register(...)` to inject your custom Stage, Provider, or Exporter.

## Distributing your Plugin

If packaging as a wheel/sdist, use the `keyword_intelligence.plugins` entry point in your `pyproject.toml` or `setup.py`:

```toml
[project.entry-points."keyword_intelligence.plugins"]
my_custom_plugin = "my_package.module:MyPluginClass"
```

The `PluginManager` will automatically discover and load it when installed in the same environment.
