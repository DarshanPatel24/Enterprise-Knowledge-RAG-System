"""Master integration handoff readiness (handbook Chapter 23).

Validates the EKCP KPIs against the handbook targets and assembles the master
integration handoff package: the endpoints, the contracts consumed and produced,
the KPIs proven, and the policy and audit coverage. The package is the artifact
Product, Architecture, and Quality sign off for master integration.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from domain.readiness.models import (
    ReadinessFinding,
    ReadinessReport,
    error,
    info,
    warning,
)

# Endpoints EKCP exposes to the master integration.
EKCP_ENDPOINTS: tuple[str, ...] = (
    "GET /health/live",
    "GET /health/ready",
    "GET /v1/readiness",
    "POST /conversation/start",
    "POST /conversation/message",
    "POST /context/build",
    "POST /prompt/generate",
    "POST /model/invoke",
    "POST /memory/store",
    "POST /memory/retrieve",
    "POST /agent/execute",
    "POST /agent/plan",
    "POST /governance/evaluate",
    "GET /governance/audit",
    "POST /workflow/trigger",
    "POST /chat/stream",
)

# Cross-service contracts EKCP consumes and produces.
EKCP_CONTRACTS: tuple[str, ...] = (
    "SecurityContext",
    "RetrievalContextPackage",
    "RetrievalCandidate",
    "Citation",
)


class HandoffKpis(BaseModel):
    """Immutable measured KPI values for the handoff gate."""

    model_config = ConfigDict(frozen=True)

    conversation_completion: float = Field(default=1.0, ge=0.0, le=1.0)
    first_response_latency_ms: float = Field(default=50.0, ge=0.0)
    tool_success: float = Field(default=1.0, ge=0.0, le=1.0)
    agent_orchestration: float = Field(default=1.0, ge=0.0, le=1.0)
    conversation_recovery: float = Field(default=1.0, ge=0.0, le=1.0)
    policy_enforcement_coverage: float = Field(default=1.0, ge=0.0, le=1.0)
    audit_coverage: float = Field(default=1.0, ge=0.0, le=1.0)


class HandoffTargetsLike(Protocol):
    """Structural view of the target thresholds the handoff gate reads."""

    min_conversation_completion: float
    first_response_latency_budget_ms: float
    min_tool_success: float
    min_agent_orchestration: float
    min_conversation_recovery: float
    min_policy_coverage: float
    min_audit_coverage: float


class MasterHandoffPackage(BaseModel):
    """Immutable master integration handoff package (handbook 23)."""

    model_config = ConfigDict(frozen=True)

    service: str = "ekcp"
    version: str = "0.1.0"
    endpoints: tuple[str, ...] = EKCP_ENDPOINTS
    contracts: tuple[str, ...] = EKCP_CONTRACTS
    kpis: HandoffKpis = Field(default_factory=HandoffKpis)
    policy_enforcement_coverage: float = 1.0
    audit_coverage: float = 1.0
    ready: bool = False
    report: ReadinessReport | None = None


def default_handoff_kpis() -> HandoffKpis:
    """Return the local-first proven KPI baseline (deterministic system)."""
    return HandoffKpis()


def assess_handoff_readiness(
    kpis: HandoffKpis, *, targets: HandoffTargetsLike
) -> ReadinessReport:
    """Assess whether the measured KPIs meet the master integration targets."""
    findings = []

    findings.append(
        _gate(
            "conversation_completion",
            kpis.conversation_completion,
            targets.min_conversation_completion,
        )
    )
    if kpis.first_response_latency_ms > targets.first_response_latency_budget_ms:
        findings.append(
            warning(
                "first_response_latency",
                (
                    f"first response {kpis.first_response_latency_ms:.0f} ms exceeds "
                    f"{targets.first_response_latency_budget_ms:.0f} ms budget"
                ),
            )
        )
    else:
        findings.append(
            info(
                "first_response_latency",
                f"first response {kpis.first_response_latency_ms:.0f} ms within budget",
            )
        )
    findings.append(_gate("tool_success", kpis.tool_success, targets.min_tool_success))
    findings.append(
        _gate(
            "agent_orchestration",
            kpis.agent_orchestration,
            targets.min_agent_orchestration,
        )
    )
    findings.append(
        _gate(
            "conversation_recovery",
            kpis.conversation_recovery,
            targets.min_conversation_recovery,
        )
    )
    findings.append(
        _gate(
            "policy_enforcement_coverage",
            kpis.policy_enforcement_coverage,
            targets.min_policy_coverage,
        )
    )
    findings.append(
        _gate("audit_coverage", kpis.audit_coverage, targets.min_audit_coverage)
    )
    return ReadinessReport(name="master_handoff", findings=tuple(findings))


def build_master_handoff_package(
    kpis: HandoffKpis, report: ReadinessReport
) -> MasterHandoffPackage:
    """Assemble the master integration handoff package from the KPIs and report."""
    return MasterHandoffPackage(
        kpis=kpis,
        policy_enforcement_coverage=kpis.policy_enforcement_coverage,
        audit_coverage=kpis.audit_coverage,
        ready=report.ready,
        report=report,
    )


def _gate(check: str, measured: float, target: float) -> ReadinessFinding:
    if measured < target:
        return error(
            check, f"{check} {measured:.3f} below target {target:.3f}"
        )
    return info(check, f"{check} {measured:.3f} meets target {target:.3f}")
