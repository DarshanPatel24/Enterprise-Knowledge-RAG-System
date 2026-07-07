"""Agent runtime models (handbook Chapter 9).

An agent is a governed execution unit (not an LLM or a prompt) with an explicit
identity, capabilities, tool permissions, and an execution contract. Agents are
selected by capability, never by name. Every model is frozen and every execution
produces a structured :class:`AgentOutcome`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from domain.tools.models import ToolInvocation


class AgentType(StrEnum):
    """Primary agent categories (handbook 9.2)."""

    PLANNER = "planner"
    SPECIALIST = "specialist"
    TOOL = "tool"
    ANALYSIS = "analysis"
    COORDINATOR = "coordinator"
    VALIDATOR = "validator"


class Capability(StrEnum):
    """Agent capability taxonomy (handbook 9.4)."""

    REASONING = "reasoning"
    PLANNING = "planning"
    RESEARCH = "research"
    RETRIEVAL = "retrieval"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    SQL_QUERYING = "sql_querying"
    DATA_ANALYSIS = "data_analysis"
    TRANSLATION = "translation"
    VALIDATION = "validation"
    REPORTING = "reporting"
    WORKFLOW_EXECUTION = "workflow_execution"


class AgentStatus(StrEnum):
    """Availability status of a registered agent (handbook 9.5-9.6)."""

    REGISTERED = "registered"
    AVAILABLE = "available"
    DEPRECATED = "deprecated"


class AgentExecutionStatus(StrEnum):
    """Outcome status of an agent execution."""

    COMPLETED = "completed"
    FAILED = "failed"


class AgentDescriptor(BaseModel):
    """Immutable registered-agent descriptor (handbook 9.5)."""

    model_config = ConfigDict(frozen=True)

    agent_id: str
    name: str
    agent_type: AgentType
    capabilities: frozenset[Capability] = frozenset()
    supported_tasks: tuple[str, ...] = ()
    tool_access: tuple[str, ...] = ()
    required_permissions: frozenset[str] = frozenset()
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    version: str = "1.0.0"
    status: AgentStatus = AgentStatus.AVAILABLE

    @property
    def is_available(self) -> bool:
        """Return whether the agent may be selected for execution."""
        return self.status is AgentStatus.AVAILABLE


class AgentRequest(BaseModel):
    """Immutable agent execution request (handbook 9.7)."""

    model_config = ConfigDict(frozen=True)

    task_description: str = Field(min_length=1)
    capability: Capability
    tenant_id: str
    prompt_text: str | None = None
    user_identity: str = ""
    correlation_id: str | None = None
    granted_permissions: frozenset[str] = frozenset()


class AgentOutcome(BaseModel):
    """Immutable structured outcome of an agent execution (handbook 9.7)."""

    model_config = ConfigDict(frozen=True)

    agent_id: str
    status: AgentExecutionStatus
    result: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    tool_usage: tuple[ToolInvocation, ...] = ()
    execution_time_ms: float = 0.0
    model_used: str = ""
    steps: int = 0
    recommended_next_actions: tuple[str, ...] = ()
    error_message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def succeeded(self) -> bool:
        """Return whether the agent execution completed successfully."""
        return self.status is AgentExecutionStatus.COMPLETED
