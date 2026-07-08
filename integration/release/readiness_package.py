"""Consolidated release-readiness package and go/no-go decision.

Assembles the engine track statuses, the integration outcomes, and the open-risk
register into one package, then derives a go/no-go recommendation: GO when no
unresolved blocking risk remains. This is the M3 consolidation artifact; it does
not launch services (evidence from M1/M2 is referenced, not re-run).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrackStatus:
    """Approval state of one delivery track."""

    track: str
    status: str  # "approved" | "conditional"
    evidence: str


@dataclass(frozen=True)
class Risk:
    """An open risk with its disposition and whether it blocks release."""

    risk_id: str
    description: str
    severity: str  # "low" | "medium" | "high" | "critical"
    blocking: bool
    disposition: str


@dataclass(frozen=True)
class ReleasePackage:
    """The consolidated release-readiness package."""

    tracks: list[TrackStatus]
    risks: list[Risk]

    @property
    def unresolved_blocking(self) -> list[Risk]:
        return [risk for risk in self.risks if risk.blocking]

    @property
    def decision(self) -> str:
        return "NO-GO" if self.unresolved_blocking else "GO"


_TRACKS: tuple[TrackStatus, ...] = (
    TrackStatus(
        "Foundation (contracts & governance)",
        "approved",
        "F1 approved; contracts frozen at v1.0.0 in packages/contracts; exit evidence recorded "
        "and validated by the M1 compatibility matrix.",
    ),
    TrackStatus("EKIE", "approved", "S0-S9 approved; 252 pytest green."),
    TrackStatus("EKRE", "approved", "S0-S8 approved; 162 pytest green."),
    TrackStatus("EKCP", "approved", "Phase 0 + S0-S8 approved; 186 pytest green."),
    TrackStatus("Web UI", "approved", "UI-S0-S3 approved; TypeScript strict build green."),
    TrackStatus(
        "Master Integration M1",
        "approved",
        "Contract matrix + live EKCP<->EKRE interface; 9 pytest green.",
    ),
    TrackStatus(
        "Master Integration M2",
        "approved",
        "Resilience + DSAR purge + readiness + web UI E2E; 14 pytest green.",
    ),
)

_RISKS: tuple[Risk, ...] = (
    Risk(
        "R1",
        "ExecutionContext contract is defined but not consumed; ids flow via headers.",
        "low",
        False,
        "Accept; revisit if a typed cross-service execution envelope is needed.",
    ),
    Risk(
        "R2",
        "DSAR purge: EnterpriseDataPurgeEvent propagation is provided by the integration "
        "PurgeOrchestrator, which now fans out to both EKCP memory purge and the EKIE batch "
        "document purge endpoint.",
        "low",
        False,
        "RESOLVED: added EKIE POST /v1/documents/purge and registered an EKIE purge adapter "
        "with the orchestrator. Residual note: EKIE data is tenant + document scoped (no user "
        "attribution), so the DSAR subscriber supplies the subject's document set.",
    ),
    Risk(
        "R3",
        "Web UI end-to-end browser-level rendering of streamed tokens and citation cards.",
        "low",
        False,
        "RESOLVED: added a Playwright browser E2E (apps/web-ui/e2e/chat.spec.ts) that drives "
        "the chat UI, intercepts the EKCP SSE contract, and asserts streamed text, a citation "
        "card with clearance badge, and the pre-chat configuration gate.",
    ),
    Risk(
        "R4",
        "Foundation track exit-evidence write-up.",
        "low",
        False,
        "RESOLVED: Foundation F1 delivery evidence recorded in the sprint track; contracts "
        "validated by the M1 matrix.",
    ),
    Risk(
        "R5",
        "Next.js dependency security posture.",
        "low",
        False,
        "RESOLVED: upgraded the web UI to Next.js 16 + React 19 (ESLint flat config) with a "
        "postcss override; npm audit reports 0 vulnerabilities; typecheck, lint, and build pass.",
    ),
)


def build_release_package() -> ReleasePackage:
    """Assemble the consolidated release-readiness package."""
    return ReleasePackage(tracks=list(_TRACKS), risks=list(_RISKS))


def render_package_markdown(package: ReleasePackage) -> str:
    """Render the release-readiness package as Markdown evidence."""
    lines = [
        "# M3 Release Readiness Package",
        "",
        "## Track Statuses",
        "",
        "| Track | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for track in package.tracks:
        lines.append(f"| {track.track} | {track.status.upper()} | {track.evidence} |")
    lines += [
        "",
        "## Open-Risk Register",
        "",
        "| ID | Severity | Blocking | Description | Disposition |",
        "| --- | --- | --- | --- | --- |",
    ]
    for risk in package.risks:
        lines.append(
            f"| {risk.risk_id} | {risk.severity} | {'yes' if risk.blocking else 'no'} | "
            f"{risk.description} | {risk.disposition} |"
        )
    return "\n".join(lines) + "\n"


def render_decision_markdown(package: ReleasePackage) -> str:
    """Render the go/no-go decision record as Markdown evidence."""
    blocking = package.unresolved_blocking
    lines = [
        "# M3 Go/No-Go Decision Record",
        "",
        f"Decision: {package.decision}",
        "",
        f"Tracks: {len(package.tracks)} "
        f"({sum(1 for t in package.tracks if t.status == 'approved')} approved, "
        f"{sum(1 for t in package.tracks if t.status == 'conditional')} conditional).",
        f"Open risks: {len(package.risks)} "
        f"({len(blocking)} unresolved blocking).",
        "",
        "## Conditions",
        "",
    ]
    if blocking:
        for risk in blocking:
            lines.append(f"- BLOCKED by {risk.risk_id}: {risk.description}")
    else:
        lines.append(
            "- No unresolved blocking risks. Release approved; every item in the open-risk "
            "register is resolved or accepted."
        )
    return "\n".join(lines) + "\n"
