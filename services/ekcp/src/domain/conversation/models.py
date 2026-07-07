"""Conversation domain models: the Conversation Digital Twin and its parts.

The Conversation Digital Twin (CDT) is the authoritative, immutable
representation of a conversation's operational state (not message content). All
models are frozen; state changes produce a new CDT via ``model_copy`` so history
and versioning stay explicit and auditable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class ConversationState(StrEnum):
    """Conversation lifecycle states (handbook Chapter 4)."""

    CREATED = "created"
    ACTIVE = "active"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    RECOVERING = "recovering"


class OwnershipModel(StrEnum):
    """Conversation ownership model."""

    INDIVIDUAL = "individual"
    SHARED = "shared"
    TEAM = "team"
    ORGANIZATION = "organization"


class InteractionType(StrEnum):
    """Type of a request-response interaction."""

    QUERY = "query"
    TASK = "task"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"
    COLLABORATION = "collaboration"
    AGENT_REQUEST = "agent_request"


class InteractionStatus(StrEnum):
    """Execution status of an interaction."""

    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"
    PAUSED = "paused"


class MessageRole(StrEnum):
    """Author role of a message."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    AGENT = "agent"
    SYSTEM = "system"


class StateTransition(BaseModel):
    """Immutable record of a single lifecycle state change."""

    model_config = ConfigDict(frozen=True)

    from_state: ConversationState
    to_state: ConversationState
    reason: str
    timestamp: datetime = Field(default_factory=_utc_now)


class ConversationMetrics(BaseModel):
    """Immutable operational metrics accumulated over a conversation."""

    model_config = ConfigDict(frozen=True)

    interaction_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_ms: float = 0.0
    agent_call_count: int = 0
    tool_call_count: int = 0
    human_intervention_count: int = 0
    error_count: int = 0
    last_error: str | None = None


class Interaction(BaseModel):
    """Immutable record of a single request-response cycle."""

    model_config = ConfigDict(frozen=True)

    interaction_id: str
    interaction_type: InteractionType
    status: InteractionStatus
    user_message: str
    assistant_response: str = ""
    tokens_used: int = 0
    cost_estimate: float = 0.0
    routing_target: str = "none"
    timestamp: datetime = Field(default_factory=_utc_now)
    duration_ms: float = 0.0


class ConversationDigitalTwin(BaseModel):
    """Authoritative, immutable operational state of a conversation."""

    model_config = ConfigDict(frozen=True)

    # Identity
    conversation_id: str
    workspace_id: str
    tenant_id: str

    # Metadata
    title: str
    owner_id: str
    participants: tuple[str, ...] = ()
    priority: str = "normal"
    labels: tuple[str, ...] = ()
    business_domain: str = ""
    security_classification: str = "internal"
    language: str = "en"
    ownership_model: OwnershipModel = OwnershipModel.INDIVIDUAL

    # Lifecycle
    current_state: ConversationState = ConversationState.CREATED
    state_transition_history: tuple[StateTransition, ...] = ()

    # Active thread and interaction
    active_thread_id: str | None = None
    active_interaction_id: str | None = None

    # Session references (pointers only)
    active_session_ids: tuple[str, ...] = ()

    # Metrics
    metrics: ConversationMetrics = Field(default_factory=ConversationMetrics)

    # Versioning (optimistic concurrency)
    version_number: int = 0
    created_date: datetime = Field(default_factory=_utc_now)
    last_activity: datetime = Field(default_factory=_utc_now)
    last_modified: datetime = Field(default_factory=_utc_now)
