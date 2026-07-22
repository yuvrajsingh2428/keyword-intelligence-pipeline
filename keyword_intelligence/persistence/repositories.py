"""Persistence layer abstractions and in-memory implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from keyword_intelligence.models import PipelineResult
from keyword_intelligence.reporting.models import ReportResult

T = TypeVar("T")


class UnitOfWork(ABC):
    """Abstraction for transaction boundaries."""

    @abstractmethod
    def begin(self) -> None:
        """Begin a new transaction."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass


class Repository(ABC, Generic[T]):
    """Generic repository interface."""

    @abstractmethod
    def get(self, id: str) -> T | None:
        """Retrieve an entity by ID."""
        pass

    @abstractmethod
    def save(self, entity: T) -> None:
        """Save an entity."""
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete an entity by ID."""
        pass


# --- Specific Interfaces ---


class PipelineExecutionRepository(Repository[PipelineResult]):
    """Repository for pipeline executions."""

    pass


class ReportRepository(Repository[ReportResult]):
    """Repository for generated reports."""

    pass


class DatasetRepository(
    Repository[Any]
):  # Any is used here to avoid pandas dependency in core
    """Repository for raw/processed datasets."""

    pass


# --- In-Memory Implementations ---


class InMemoryUnitOfWork(UnitOfWork):
    """In-memory Unit of Work (no-op)."""

    def begin(self) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


class InMemoryRepository(Repository[T]):
    """Generic in-memory store."""

    def __init__(self) -> None:
        self._store: dict[str, T] = {}

    def get(self, id: str) -> T | None:
        return self._store.get(id)

    def save(self, entity: T) -> None:
        # Assumes entities have an execution_id or id attribute
        ent_id = getattr(entity, "execution_id", getattr(entity, "id", None))
        if not ent_id:
            raise ValueError("Entity must have an execution_id or id attribute")
        self._store[ent_id] = entity

    def delete(self, id: str) -> None:
        if id in self._store:
            del self._store[id]


class InMemoryPipelineExecutionRepository(
    InMemoryRepository[PipelineResult], PipelineExecutionRepository
):
    """In-memory execution storage."""

    pass


class InMemoryReportRepository(InMemoryRepository[ReportResult], ReportRepository):
    """In-memory report storage."""

    pass


class InMemoryDatasetRepository(InMemoryRepository[Any], DatasetRepository):
    """In-memory dataset storage."""

    def save(self, entity: Any) -> None:
        # Datasets need a specific identifier handling if passed as tuple (id, df)
        if isinstance(entity, tuple) and len(entity) == 2:
            self._store[entity[0]] = entity[1]
        else:
            raise ValueError(
                "In-memory dataset repository expects a tuple (id, dataframe)"
            )
