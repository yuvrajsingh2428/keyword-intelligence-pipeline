"""Event Bus for decoupled pub/sub event handling."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger


class EventBus:
    """Simple synchronous event bus for observability events."""

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: dict[str, list[Callable[..., Any]]] = {}

    def subscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        """Subscribe a handler to an event."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """Publish an event to all subscribers synchronously."""
        handlers = self._subscribers.get(event_name, [])
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Event handler {handler.__name__} failed "
                    f"on event {event_name}: {e}"
                )
