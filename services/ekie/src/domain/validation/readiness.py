"""Deployment, HA, and disaster-recovery readiness assessment (EKIE-S9-4).

Produces an advisory :class:`ValidationReport` describing whether configuration
satisfies non-functional and operational criteria. The assessment is
local-first: a local environment is fully deployable with self-hosted tooling
and no Kubernetes dependency, while non-local environments surface stricter
findings for credentials, high availability, and observability.
"""

from __future__ import annotations

from config.settings import EkieSettings
from domain.validation.report import ValidationReport, error, info, warning

_LOCAL = "local"


def assess_readiness(settings: EkieSettings) -> ValidationReport:
    """Assess deployment, HA, and DR readiness from configuration."""
    findings = []
    is_local = settings.environment == _LOCAL
    deployment = settings.deployment

    if not 0.0 < deployment.min_success_rate <= 1.0:
        findings.append(
            error(
                "readiness.nfr",
                f"min_success_rate {deployment.min_success_rate} must be in (0, 1]",
            )
        )
    if deployment.max_stage_latency_seconds <= 0:
        findings.append(
            error(
                "readiness.nfr",
                "max_stage_latency_seconds must be positive",
            )
        )
    if deployment.rpo_seconds <= 0 or deployment.rto_seconds <= 0:
        findings.append(
            error("readiness.dr", "rpo_seconds and rto_seconds must be positive")
        )
    elif deployment.rto_seconds < deployment.rpo_seconds:
        findings.append(
            error(
                "readiness.dr",
                f"rto_seconds {deployment.rto_seconds} is below rpo_seconds "
                f"{deployment.rpo_seconds}",
            )
        )

    if is_local:
        findings.append(
            info(
                "readiness.deployment",
                "local-first deployment is self-contained; no Kubernetes required",
            )
        )
        if deployment.replicas < 1:
            findings.append(
                error("readiness.ha", "replicas must be at least 1")
            )
    else:
        if deployment.replicas < 2:
            findings.append(
                warning(
                    "readiness.ha",
                    "replicas < 2 provides no high availability in non-local "
                    "environments",
                )
            )
        if not settings.storage.access_key or not settings.storage.secret_key:
            findings.append(
                error(
                    "readiness.storage",
                    "object storage credentials are required outside local",
                )
            )
        if settings.control_plane.url is None:
            findings.append(
                warning(
                    "readiness.control_plane",
                    "control-plane URL not set; using host-based defaults",
                )
            )
        if not settings.observability.langfuse_enabled:
            findings.append(
                warning(
                    "readiness.observability",
                    "Langfuse tracing disabled outside local environment",
                )
            )

    if not any(f.check.startswith("readiness.nfr") for f in findings):
        findings.append(
            info(
                "readiness.nfr",
                f"NFR targets set: success_rate>={deployment.min_success_rate}, "
                f"p95<={deployment.max_stage_latency_seconds}s",
            )
        )
    return ValidationReport(name="readiness", findings=tuple(findings))
