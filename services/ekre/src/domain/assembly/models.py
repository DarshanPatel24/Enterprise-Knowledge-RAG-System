"""Context assembly models (handbook Chapters 26-27).

Assembly selects and organizes ranked knowledge within a token budget and
packages the model-agnostic Retrieval Context Package handed to EKCP. The
package (``contracts.retrieval.RetrievalContextPackage``) is the canonical
handoff; the metrics below make the assembly auditable and observable.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from contracts.retrieval import RetrievalContextPackage


class ContextMetrics(BaseModel):
    """Auditable metrics describing how the context was assembled."""

    model_config = ConfigDict(frozen=True)

    considered_count: int = Field(ge=0)
    selected_count: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    token_budget: int = Field(ge=0)
    dropped_for_budget: int = Field(ge=0)
    dropped_duplicates: int = Field(ge=0)
    dropped_below_relevance: int = Field(ge=0)
    ordering: str = "rank"


class AssemblyResult(BaseModel):
    """The assembled context: the EKCP handoff package plus assembly metrics."""

    model_config = ConfigDict(frozen=True)

    package: RetrievalContextPackage
    metrics: ContextMetrics
    warnings: tuple[str, ...] = ()
