"""Tool execution platform models (handbook Chapter 10).

Tools expose governed business capabilities behind a standardized execution
contract; agents request capabilities but never call external systems directly.
Every model is frozen and every execution produces an auditable
:class:`ToolResult` with timing and retry accounting.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ToolCategory(StrEnum):
    """Tool categories (handbook 10.2)."""

    INFORMATION_RETRIEVAL = "information_retrieval"
    DATA_QUERY = "data_query"
    BUSINESS_ACTION = "business_action"
    INTEGRATION = "integration"
    AI_SERVICE = "ai_service"
    UTILITY = "utility"


class ToolHealth(StrEnum):
    """Operational health of a registered tool."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ToolExecutionStatus(StrEnum):
    """Outcome status of a tool execution (handbook 10.6)."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"


class ToolDescriptor(BaseModel):
    """Immutable registered-tool descriptor (handbook 10.3-10.4)."""

    model_config = ConfigDict(frozen=True)

    tool_id: str
    name: str
    capability: str
    description: str = ""
    category: ToolCategory = ToolCategory.UTILITY
    version: str = "1.0.0"
    required_permissions: frozenset[str] = frozenset()
    timeout_seconds: float = Field(default=10.0, gt=0.0)
    retry_max_attempts: int = Field(default=1, ge=1)
    health_status: ToolHealth = ToolHealth.HEALTHY


class ToolRequest(BaseModel):
    """Immutable tool execution request (handbook 10.6)."""

    model_config = ConfigDict(frozen=True)

    tool_id: str
    request_payload: dict[str, object] = Field(default_factory=dict)
    tenant_id: str = ""
    agent_identity: str = ""
    user_identity: str = ""
    correlation_id: str | None = None
    granted_permissions: frozenset[str] = frozenset()


class ToolResult(BaseModel):
    """Immutable, normalized, auditable tool execution result (handbook 10.6)."""

    model_config = ConfigDict(frozen=True)

    tool_id: str
    status: ToolExecutionStatus
    result_payload: dict[str, object] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    retry_attempts: int = 0
    error_code: str = ""
    error_message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def succeeded(self) -> bool:
        """Return whether the tool executed successfully."""
        return self.status is ToolExecutionStatus.SUCCESS


class ToolInvocation(BaseModel):
    """Immutable summary of one tool invocation for agent tool-usage tracking."""

    model_config = ConfigDict(frozen=True)

    tool_id: str
    status: ToolExecutionStatus
    duration_ms: float = 0.0
