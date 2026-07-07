"""Memory framework models: the tiered memory item and its enumerations.

Memory is organized into scoped tiers (handbook Chapter 8), from short-lived
working memory to indefinite organizational memory. Every item is immutable and
carries lineage (which conversation and validation method produced it), a
confidence derived from that validation method, and a governance classification.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class MemoryScope(StrEnum):
    """Memory tiers ordered from most transient to most durable (handbook 8.5-8.12)."""

    WORKING = "working"
    SESSION = "session"
    CONVERSATION = "conversation"
    WORKSPACE = "workspace"
    USER = "user"
    ORGANIZATIONAL = "organizational"


class MemoryType(StrEnum):
    """Classification of what a memory represents."""

    FACT = "fact"
    DECISION = "decision"
    PREFERENCE = "preference"
    PROCEDURE = "procedure"
    INSIGHT = "insight"
    RELATIONSHIP = "relationship"


class MemoryStatus(StrEnum):
    """Lifecycle status of a memory item."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


class ValidationMethod(StrEnum):
    """How a memory was validated, which determines its confidence."""

    USER_CONFIRMED = "user_confirmed"
    TOOL_VERIFIED = "tool_verified"
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    AGENT_GENERATED = "agent_generated"
    LLM_INFERRED = "llm_inferred"


class CompressionLevel(StrEnum):
    """Consolidation compression levels (handbook 8.16)."""

    SUMMARY = "summary"
    ABSTRACT = "abstract"


class MemoryItem(BaseModel):
    """Immutable, scoped, governed memory record."""

    model_config = ConfigDict(frozen=True)

    memory_id: str
    tenant_id: str
    scope: MemoryScope
    content: str
    memory_type: MemoryType
    topic: str = ""
    tags: tuple[str, ...] = ()
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    classification: str = "internal"
    status: MemoryStatus = MemoryStatus.ACTIVE
    source_validation_method: ValidationMethod = ValidationMethod.LLM_INFERRED
    source_conversation_id: str | None = None
    source_interaction_id: str | None = None
    conversation_id: str | None = None
    workspace_id: str | None = None
    user_id: str | None = None
    related_memories: tuple[str, ...] = ()
    retrieval_count: int = 0
    version: int = 1
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    last_retrieved_at: datetime | None = None
    expires_at: datetime | None = None

    def is_expired(self, *, now: datetime) -> bool:
        """Return whether the item has passed its expiration time."""
        return self.expires_at is not None and now >= self.expires_at


class ScoredMemory(BaseModel):
    """Immutable memory item paired with its retrieval relevance score."""

    model_config = ConfigDict(frozen=True)

    item: MemoryItem
    score: float = Field(ge=0.0, le=1.0)
