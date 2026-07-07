"""Tool executor: the governed tool execution pipeline (handbook 10.9).

Runs the standardized pipeline: validate, authorize (permission gate), execute
via the tool with bounded retries, normalize the result, and audit. Every
outcome is a :class:`ToolResult`; failures are isolated and never raise past the
executor except for authorization and unknown-tool errors.
"""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from domain.observability import get_logger
from domain.tools.errors import ToolError, ToolErrorType, ToolExecutionFailed
from domain.tools.models import (
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from domain.tools.permission import PermissionGate
from domain.tools.policy import ToolPolicy
from domain.tools.registry import ToolRegistry

logger = get_logger("ekcp.tools.executor")


class ToolExecutor:
    """Execute tools through the governed pipeline with permission checks."""

    def __init__(
        self,
        registry: ToolRegistry,
        policy: ToolPolicy,
        *,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        self._registry = registry
        self._policy = policy
        self._gate = PermissionGate(enforce=policy.enforce_permissions)
        self._clock = clock

    def execute(self, request: ToolRequest) -> ToolResult:
        """Run the tool execution pipeline and return the normalized result."""
        tool = self._registry.get(request.tool_id)
        self._gate.authorize(tool.descriptor, request.granted_permissions)

        max_attempts = max(self._policy.max_attempts, tool.descriptor.retry_max_attempts)
        start = self._clock()
        last_error: ToolExecutionFailed | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                payload = tool.execute(dict(request.request_payload))
            except ToolExecutionFailed as exc:
                last_error = exc
                logger.warning(
                    "tool_execution_retry",
                    extra={"tool_id": request.tool_id, "attempt": attempt},
                )
                continue
            elapsed_ms = (self._clock() - start) * 1000.0
            logger.info(
                "tool_executed",
                extra={"tool_id": request.tool_id, "attempts": attempt},
            )
            return ToolResult(
                tool_id=request.tool_id,
                status=ToolExecutionStatus.SUCCESS,
                result_payload=payload,
                execution_time_ms=round(elapsed_ms, 3),
                retry_attempts=attempt - 1,
            )

        elapsed_ms = (self._clock() - start) * 1000.0
        message = last_error.message if last_error else "tool execution failed"
        error_code = last_error.error_code if last_error else "execution_failed"
        return ToolResult(
            tool_id=request.tool_id,
            status=ToolExecutionStatus.FAILED,
            execution_time_ms=round(elapsed_ms, 3),
            retry_attempts=max_attempts - 1,
            error_code=error_code,
            error_message=message,
        )

    def try_execute(self, request: ToolRequest) -> ToolResult:
        """Execute a tool, converting authorization errors into a result.

        Used by the agent runtime so an unauthorized or unknown tool degrades to
        a failed result rather than raising into the agent loop.
        """
        try:
            return self.execute(request)
        except ToolError as exc:
            status = (
                ToolExecutionStatus.UNAUTHORIZED
                if exc.error_type is ToolErrorType.UNAUTHORIZED
                else ToolExecutionStatus.FAILED
            )
            return ToolResult(
                tool_id=request.tool_id,
                status=status,
                error_code=exc.error_type,
                error_message=exc.message,
            )
