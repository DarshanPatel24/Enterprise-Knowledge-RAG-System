"""Agent runtime: governed execution on a Sequential or LangGraph runner.

The runtime executes a selected agent through a bounded loop: an optional
permitted tool step (agents never call systems directly) followed by a reasoning
step via the model gateway. Steps are bounded to prevent runaway loops. The
Sequential runner is the local-first offline default; the LangGraph runner adds a
checkpointer for recovery and a conditional fallback edge, imported lazily.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from time import perf_counter
from typing import TypedDict

from domain.agents.errors import AgentError, AgentErrorType
from domain.agents.models import (
    AgentDescriptor,
    AgentExecutionStatus,
    AgentOutcome,
    AgentRequest,
    Capability,
)
from domain.agents.policy import AgentPolicy
from domain.gateway import GatewayError, GenerationRequest, LLMGateway
from domain.observability import get_logger
from domain.tools import (
    ToolExecutor,
    ToolInvocation,
    ToolRequest,
)


class _AgentGraphState(TypedDict, total=False):
    """LangGraph agent graph state."""

    outcome: AgentOutcome | None
    attempted_fallback: bool


logger = get_logger("ekcp.agents.runtime")

_TOOL_CAPABILITIES = frozenset({Capability.RESEARCH, Capability.RETRIEVAL})


def _build_prompt(
    descriptor: AgentDescriptor, request: AgentRequest, evidence: str
) -> str:
    lines = [
        f"You are {descriptor.name}, a governed enterprise agent.",
        f"Task: {request.task_description}",
    ]
    if evidence:
        lines.append(f"Evidence: {evidence}")
    lines.append("User request: provide a grounded, policy-compliant response.")
    return "\n".join(lines)


def execute_agent(
    descriptor: AgentDescriptor,
    request: AgentRequest,
    *,
    gateway: LLMGateway,
    tool_executor: ToolExecutor,
    max_steps: int,
    base_confidence: float,
    clock: Callable[[], float] = perf_counter,
) -> AgentOutcome:
    """Run a bounded agent loop (optional tool step then reasoning) and return the outcome."""
    start = clock()
    steps = 0
    tool_usage: list[ToolInvocation] = []
    evidence = ""

    use_tool = (
        request.capability in _TOOL_CAPABILITIES
        and "knowledge_search" in descriptor.tool_access
    )
    if use_tool:
        steps += 1
        if steps > max_steps:
            return _failed(
                descriptor, "step budget exhausted before tool step", start, clock, steps
            )
        tool_result = tool_executor.try_execute(
            ToolRequest(
                tool_id="knowledge_search",
                request_payload={"query": request.task_description},
                tenant_id=request.tenant_id,
                agent_identity=descriptor.agent_id,
                user_identity=request.user_identity,
                correlation_id=request.correlation_id,
                granted_permissions=request.granted_permissions,
            )
        )
        tool_usage.append(
            ToolInvocation(
                tool_id=tool_result.tool_id,
                status=tool_result.status,
                duration_ms=tool_result.execution_time_ms,
            )
        )
        if tool_result.succeeded:
            evidence = str(tool_result.result_payload.get("results", ""))

    steps += 1
    if steps > max_steps:
        return _failed(
            descriptor, "step budget exhausted before reasoning step", start, clock, steps
        )
    prompt = request.prompt_text or _build_prompt(descriptor, request, evidence)
    try:
        response = gateway.invoke(
            GenerationRequest(
                prompt_text=prompt,
                tenant_id=request.tenant_id,
                correlation_id=request.correlation_id,
            )
        )
    except GatewayError as exc:
        logger.warning(
            "agent_generation_failed",
            extra={"agent_id": descriptor.agent_id, "error": exc.message},
        )
        return AgentOutcome(
            agent_id=descriptor.agent_id,
            status=AgentExecutionStatus.FAILED,
            confidence_score=0.0,
            tool_usage=tuple(tool_usage),
            execution_time_ms=round((clock() - start) * 1000.0, 3),
            steps=steps,
            recommended_next_actions=("retry with a fallback model",),
            error_message=exc.message,
        )

    tool_ok = all(usage.status.value == "success" for usage in tool_usage)
    confidence = base_confidence if tool_ok else max(0.0, base_confidence - 0.25)
    logger.info(
        "agent_executed",
        extra={"agent_id": descriptor.agent_id, "steps": steps, "model": response.model_id},
    )
    return AgentOutcome(
        agent_id=descriptor.agent_id,
        status=AgentExecutionStatus.COMPLETED,
        result=response.output_text,
        confidence_score=round(confidence, 4),
        tool_usage=tuple(tool_usage),
        execution_time_ms=round((clock() - start) * 1000.0, 3),
        model_used=response.model_id,
        steps=steps,
    )


def _failed(
    descriptor: AgentDescriptor,
    message: str,
    start: float,
    clock: Callable[[], float],
    steps: int,
) -> AgentOutcome:
    return AgentOutcome(
        agent_id=descriptor.agent_id,
        status=AgentExecutionStatus.FAILED,
        execution_time_ms=round((clock() - start) * 1000.0, 3),
        steps=steps,
        recommended_next_actions=("reduce task complexity or raise the step budget",),
        error_message=message,
    )


class AgentRuntime(ABC):
    """Executes a selected agent and returns its structured outcome."""

    @abstractmethod
    def run(
        self,
        descriptor: AgentDescriptor,
        request: AgentRequest,
        *,
        gateway: LLMGateway,
        tool_executor: ToolExecutor,
        policy: AgentPolicy,
    ) -> AgentOutcome:
        """Run the agent and return its outcome."""


class SequentialAgentRunner(AgentRuntime):
    """Deterministic in-process agent runner (offline default)."""

    def run(
        self,
        descriptor: AgentDescriptor,
        request: AgentRequest,
        *,
        gateway: LLMGateway,
        tool_executor: ToolExecutor,
        policy: AgentPolicy,
    ) -> AgentOutcome:
        return execute_agent(
            descriptor,
            request,
            gateway=gateway,
            tool_executor=tool_executor,
            max_steps=policy.max_steps,
            base_confidence=policy.base_confidence,
        )


class LangGraphAgentRunner(AgentRuntime):
    """LangGraph-backed runner with a checkpointer and a conditional fallback edge."""

    def run(
        self,
        descriptor: AgentDescriptor,
        request: AgentRequest,
        *,
        gateway: LLMGateway,
        tool_executor: ToolExecutor,
        policy: AgentPolicy,
    ) -> AgentOutcome:
        try:
            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.graph import END, START, StateGraph
        except ImportError as exc:
            raise AgentError(
                AgentErrorType.RUNNER_UNAVAILABLE,
                "langgraph is not installed; set EKCP_AGENT__RUNNER=sequential",
            ) from exc

        def _run_once() -> AgentOutcome:
            return execute_agent(
                descriptor,
                request,
                gateway=gateway,
                tool_executor=tool_executor,
                max_steps=policy.max_steps,
                base_confidence=policy.base_confidence,
            )

        def _act(_state: _AgentGraphState) -> _AgentGraphState:
            return {"outcome": _run_once()}

        def _fallback(_state: _AgentGraphState) -> _AgentGraphState:
            return {"outcome": _run_once(), "attempted_fallback": True}

        def _route(state: _AgentGraphState) -> str:
            outcome = state.get("outcome")
            if (
                outcome is not None
                and not outcome.succeeded
                and not state.get("attempted_fallback", False)
            ):
                return "fallback"
            return END

        builder = StateGraph(_AgentGraphState)
        builder.add_node("act", _act)  # type: ignore[call-overload]
        builder.add_node("fallback", _fallback)  # type: ignore[call-overload]
        builder.add_edge(START, "act")
        builder.add_conditional_edges("act", _route, {"fallback": "fallback", END: END})
        builder.add_edge("fallback", END)
        graph = builder.compile(checkpointer=MemorySaver())

        config = {
            "configurable": {
                "thread_id": f"{request.tenant_id}:{descriptor.agent_id}",
            },
        }
        result = graph.invoke({}, config=config)  # type: ignore[call-overload]
        outcome = result.get("outcome")
        if not isinstance(outcome, AgentOutcome):
            raise AgentError(
                AgentErrorType.EXECUTION_FAILED, "agent graph produced no outcome"
            )
        return outcome


def runner_from_policy(policy: AgentPolicy) -> AgentRuntime:
    """Return the configured agent runner (sequential default, langgraph optional)."""
    if policy.runner == "langgraph":
        return LangGraphAgentRunner()
    return SequentialAgentRunner()
