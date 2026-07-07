"""In-memory Execution Context Package store.

Persists assembled context packages by ``(tenant_id, context_id)`` so a prompt
request can reference a previously built context. The in-memory store is the
local-first offline default; a cache-backed store is wired behind this interface
in a later sprint.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.context.errors import ContextError, ContextErrorType
from domain.context.models import ExecutionContextPackage


class ContextStore(ABC):
    """Abstract context package store keyed by tenant and context id."""

    @abstractmethod
    def get(self, tenant_id: str, context_id: str) -> ExecutionContextPackage:
        """Return the stored context package, or raise ``NOT_FOUND``."""

    @abstractmethod
    def save(self, package: ExecutionContextPackage) -> None:
        """Persist a context package."""


class InMemoryContextStore(ContextStore):
    """Deterministic in-memory context package store (local-first default)."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], ExecutionContextPackage] = {}

    def get(self, tenant_id: str, context_id: str) -> ExecutionContextPackage:
        package = self._items.get((tenant_id, context_id))
        if package is None:
            raise ContextError(
                ContextErrorType.NOT_FOUND,
                f"context {context_id} not found for tenant {tenant_id}",
            )
        return package

    def save(self, package: ExecutionContextPackage) -> None:
        self._items[(package.tenant_id, package.context_id)] = package
