"""Checkpointer abstraction for workflow resume and dead-letter recovery.

The orchestrator persists a workflow snapshot after every stage so an
interrupted or dead-lettered workflow can resume from its last good state
without repeating completed, idempotent stages (handbook 6.20). The default
in-memory implementation keeps the offline path dependency-free; a durable
implementation can be swapped in without touching the orchestrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.orchestration.state import WorkflowState


class Checkpointer(ABC):
    """Persists and restores workflow state snapshots keyed by tenant/document."""

    @abstractmethod
    def save(self, state: WorkflowState) -> None:
        """Persist the latest snapshot for a workflow."""

    @abstractmethod
    def load(self, tenant_id: str, document_id: str) -> WorkflowState | None:
        """Return the latest snapshot for a workflow, or ``None`` if absent."""

    @abstractmethod
    def delete(self, tenant_id: str, document_id: str) -> None:
        """Discard any stored snapshot for a workflow."""


class InMemoryCheckpointer(Checkpointer):
    """Process-local checkpointer used for offline runs and tests."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], WorkflowState] = {}

    def save(self, state: WorkflowState) -> None:
        """Persist the latest snapshot for a workflow."""
        self._store[(state.tenant_id, state.document_id)] = state

    def load(self, tenant_id: str, document_id: str) -> WorkflowState | None:
        """Return the latest snapshot for a workflow, or ``None`` if absent."""
        return self._store.get((tenant_id, document_id))

    def delete(self, tenant_id: str, document_id: str) -> None:
        """Discard any stored snapshot for a workflow."""
        self._store.pop((tenant_id, document_id), None)
