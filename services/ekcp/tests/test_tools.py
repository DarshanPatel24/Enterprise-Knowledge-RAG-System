"""Tests for the tool execution platform: registry, permissions, executor."""

from __future__ import annotations

from config.settings import ToolSettings
from domain.tools import (
    ToolExecutionStatus,
    ToolExecutor,
    ToolPolicy,
    ToolRequest,
    default_tool_registry,
)


def _executor(**overrides: object) -> ToolExecutor:
    settings = ToolSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return ToolExecutor(default_tool_registry(), ToolPolicy.from_settings(settings))


def test_discover_by_capability_respects_permissions() -> None:
    registry = default_tool_registry()
    without = registry.discover(capability="knowledge_search")
    granted = registry.discover(
        capability="knowledge_search",
        granted_permissions=frozenset({"tool:knowledge_search"}),
    )
    assert without == []
    assert [d.tool_id for d in granted] == ["knowledge_search"]


def test_execute_authorized_tool() -> None:
    result = _executor().execute(
        ToolRequest(
            tool_id="knowledge_search",
            request_payload={"query": "remote work policy"},
            tenant_id="tenant-a",
            granted_permissions=frozenset({"tool:knowledge_search"}),
        )
    )
    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.result_payload["result_count"] == 1


def test_permission_denied_raises_via_try_execute() -> None:
    result = _executor().try_execute(
        ToolRequest(
            tool_id="knowledge_search",
            request_payload={"query": "x"},
            tenant_id="tenant-a",
        )
    )
    assert result.status is ToolExecutionStatus.UNAUTHORIZED


def test_permission_enforcement_can_be_disabled() -> None:
    result = _executor(enforce_permissions=False).execute(
        ToolRequest(tool_id="knowledge_search", request_payload={"query": "x"})
    )
    assert result.status is ToolExecutionStatus.SUCCESS


def test_failing_tool_reports_failure_after_retries() -> None:
    # Missing query makes the knowledge tool raise; the executor retries then fails.
    result = _executor(enforce_permissions=False, max_attempts=3).execute(
        ToolRequest(tool_id="knowledge_search", request_payload={})
    )
    assert result.status is ToolExecutionStatus.FAILED
    assert result.retry_attempts == 2
    assert result.error_code == "missing_query"


def test_calculator_tool() -> None:
    result = _executor().execute(
        ToolRequest(tool_id="calculator", request_payload={"operands": [1, 2, 3]})
    )
    assert result.result_payload["sum"] == 6.0
