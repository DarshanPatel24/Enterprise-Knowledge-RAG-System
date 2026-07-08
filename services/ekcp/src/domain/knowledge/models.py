"""Knowledge integration models: the retrieval result and its degradation state."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from contracts.retrieval import RetrievalContextPackage


class KnowledgeResult(BaseModel):
    """Immutable outcome of an enterprise knowledge retrieval attempt.

    ``package`` is the retrieved knowledge, or ``None`` when EKRE was
    unavailable and the caller must degrade to local memory. ``degraded`` records
    that the platform fell back rather than failing the session.
    """

    model_config = ConfigDict(frozen=True)

    package: RetrievalContextPackage | None = None
    degraded: bool = False
    reason: str = ""
    candidate_count: int = 0
    latency_ms: float = 0.0

    @property
    def has_knowledge(self) -> bool:
        """Return whether enterprise knowledge was successfully retrieved."""
        return self.package is not None and bool(self.package.candidates)
