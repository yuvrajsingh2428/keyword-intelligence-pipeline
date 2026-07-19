"""Trace context for distributed tracing and context propagation."""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import Field

from keyword_intelligence.models.base import AppBaseModel


class TraceContext(AppBaseModel):
    """Context carrying trace information across pipeline boundaries."""

    trace_id: str
    execution_id: str
    parent_id: str | None = None
    timestamp: float
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(cls, execution_id: str | None = None) -> TraceContext:
        """Create a new trace context."""
        return cls(
            trace_id=str(uuid.uuid4()),
            execution_id=execution_id or str(uuid.uuid4()),
            timestamp=time.time(),
        )

    def spawn(self) -> TraceContext:
        """Spawn a child trace context."""
        return TraceContext(
            trace_id=str(uuid.uuid4()),
            execution_id=self.execution_id,
            parent_id=self.trace_id,
            timestamp=time.time(),
            metadata=self.metadata.copy(),
        )
