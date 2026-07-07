"""Worker registry: dynamic registration and discovery (handbook Chapter 18.7)."""

from __future__ import annotations

from domain.execution.worker import RetrievalWorker
from domain.query.models import RetrievalEngineType


class WorkerRegistry:
    """Registers retrieval workers and resolves them by engine type."""

    def __init__(self) -> None:
        self._workers: dict[RetrievalEngineType, RetrievalWorker] = {}

    def register(self, worker: RetrievalWorker) -> None:
        """Register a worker under the engine type it advertises."""
        self._workers[worker.descriptor.engine] = worker

    def get(self, engine: RetrievalEngineType) -> RetrievalWorker | None:
        """Return the worker registered for ``engine``, or ``None``."""
        return self._workers.get(engine)

    def has(self, engine: RetrievalEngineType) -> bool:
        """Return whether a worker is registered for ``engine``."""
        return engine in self._workers

    def engines(self) -> tuple[RetrievalEngineType, ...]:
        """Return the engine types with a registered worker."""
        return tuple(self._workers)


def default_worker_registry() -> WorkerRegistry:
    """Return an empty registry.

    Real vector/keyword/metadata workers are registered in S3. Tests and the
    demo register deterministic :class:`StaticRetrievalWorker` instances.
    """
    return WorkerRegistry()
