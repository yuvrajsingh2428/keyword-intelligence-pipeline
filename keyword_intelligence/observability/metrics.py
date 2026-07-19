"""Metrics collector for application-level observability."""

from __future__ import annotations

from typing import Any


class MetricsCollector:
    """In-memory metrics collector."""

    def __init__(self) -> None:
        """Initialize metric counters and timers."""
        self._counters: dict[str, int] = {}
        self._timers: dict[str, list[float]] = {}

    def increment(self, metric: str, amount: int = 1) -> None:
        """Increment a counter metric."""
        self._counters[metric] = self._counters.get(metric, 0) + amount

    def record_time(self, metric: str, duration_ms: float) -> None:
        """Record an execution duration."""
        if metric not in self._timers:
            self._timers[metric] = []
        self._timers[metric].append(duration_ms)

    def get_snapshot(self) -> dict[str, Any]:
        """Get a point-in-time snapshot of all metrics."""
        return {
            "counters": dict(self._counters),
            "timers": {
                m: {
                    "count": len(t),
                    "avg_ms": sum(t) / len(t) if t else 0,
                    "max_ms": max(t) if t else 0,
                }
                for m, t in self._timers.items()
            },
        }

    def reset(self) -> None:
        """Clear all metrics."""
        self._counters.clear()
        self._timers.clear()
