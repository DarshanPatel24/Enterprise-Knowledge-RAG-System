"""Retrieval worker framework contract (handbook Chapter 18).

Every retrieval capability is implemented as a worker that executes a
standardized task and returns standardized candidates. Workers are pure with
respect to a task: they perform no planning, ranking, or context assembly. The
framework (see ``lifecycle.py``) wraps every worker call in the standard
lifecycle, timing, and failure isolation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from contracts.retrieval import RetrievalCandidate
from contracts.security_context import SecurityContext
from domain.execution.models import RetrievalTask, WorkerDescriptor
from domain.query.models import RetrievalEngineType


class RetrievalWorker(ABC):
    """Abstract retrieval worker: executes one task, returns candidates."""

    @property
    @abstractmethod
    def descriptor(self) -> WorkerDescriptor:
        """Return the worker's capability advertisement."""

    @abstractmethod
    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        """Execute the task and return candidates.

        Implementations raise :class:`WorkerError` for controlled failures; any
        exception is isolated by the framework and never terminates the query.
        """


class StaticRetrievalWorker(RetrievalWorker):
    """Deterministic worker returning a fixed candidate set.

    A local-first framework primitive used for tests, demos, and offline
    execution. Real vector/keyword/metadata workers are delivered in S3.
    """

    def __init__(
        self,
        engine: RetrievalEngineType,
        candidates: Sequence[RetrievalCandidate],
        *,
        worker_id: str | None = None,
        version: str = "1.0.0",
    ) -> None:
        self._descriptor = WorkerDescriptor(
            worker_id=worker_id or f"static-{engine.value}",
            engine=engine,
            version=version,
            supported_task_types=(engine.value,),
        )
        self._candidates = tuple(candidates)

    @property
    def descriptor(self) -> WorkerDescriptor:
        """Return the worker's capability advertisement."""
        return self._descriptor

    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        """Return the fixed candidate set (clamped later by the framework)."""
        return self._candidates
