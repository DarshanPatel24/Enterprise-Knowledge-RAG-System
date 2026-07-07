"""Context orchestration models: context items and the Execution Context Package.

Assembly produces an immutable Execution Context Package (ECP): the governed,
ranked, token-bounded context handed to prompt orchestration before generation.
Every included item carries lineage (source, reason, rank, policy status) so the
assembled context is fully auditable. Citations are preserved verbatim.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from contracts.retrieval import Citation


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class ContextSource(StrEnum):
    """Named context sources assembled before generation (handbook Chapter 6)."""

    CONVERSATION = "conversation"
    MEMORY = "memory"
    WORKSPACE = "workspace"
    ENTERPRISE = "enterprise"
    TOOL = "tool"
    POLICY = "policy"
    AGENT = "agent"


class PolicyStatus(StrEnum):
    """Governance status of a context item."""

    ALLOWED = "allowed"
    FILTERED = "filtered"
    COMPRESSED = "compressed"


class ContextItem(BaseModel):
    """Immutable single unit of assembled context with lineage."""

    model_config = ConfigDict(frozen=True)

    source: ContextSource
    content: str
    reason: str
    rank_score: float = Field(ge=0.0, le=1.0)
    policy_status: PolicyStatus = PolicyStatus.ALLOWED
    token_estimate: int = 0
    citation: Citation | None = None
    freshness: datetime = Field(default_factory=_utc_now)


class ContextLineageItem(BaseModel):
    """Immutable audit record for one item's inclusion decision."""

    model_config = ConfigDict(frozen=True)

    source: ContextSource
    reason: str
    rank_score: float
    policy_status: PolicyStatus


class ContextMetrics(BaseModel):
    """Immutable quality and budgeting metrics for an assembled context."""

    model_config = ConfigDict(frozen=True)

    considered_count: int = 0
    selected_count: int = 0
    dropped_for_budget: int = 0
    dropped_below_relevance: int = 0
    dropped_duplicates: int = 0
    dropped_citation_unready: int = 0
    total_tokens: int = 0
    token_budget: int = 0
    source_diversity: int = 0


class ExecutionContextPackage(BaseModel):
    """Immutable, governed, token-bounded context delivered to prompt orchestration."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    tenant_id: str
    conversation_id: str
    user_intent: str
    items: tuple[ContextItem, ...] = ()
    lineage: tuple[ContextLineageItem, ...] = ()
    metrics: ContextMetrics = Field(default_factory=ContextMetrics)
    compression_applied: bool = False
    security_filtered: bool = True
    warnings: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=_utc_now)
