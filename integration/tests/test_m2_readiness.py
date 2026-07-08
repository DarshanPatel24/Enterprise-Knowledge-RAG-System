"""M2-S3: consolidated SLO/SLA operational readiness across the engines."""

from __future__ import annotations

from pathlib import Path

from harness.readiness import ReadinessTarget, aggregate_readiness, render_markdown

_EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"


def test_all_engines_report_ready(all_engines: dict[str, str]) -> None:
    targets = [
        ReadinessTarget("ekcp", all_engines["ekcp"], "/v1/readiness"),
        ReadinessTarget("ekre", all_engines["ekre"], "/v1/readiness"),
        ReadinessTarget("ekie", all_engines["ekie"], "/health/ready"),
    ]
    report = aggregate_readiness(targets)

    _EVIDENCE_DIR.mkdir(exist_ok=True)
    (_EVIDENCE_DIR / "m2_readiness_report.md").write_text(
        render_markdown(report), encoding="utf-8"
    )

    not_ready = [probe.engine for probe in report.probes if not probe.ready]
    assert report.all_ready, f"engines not ready: {not_ready}"
    assert {probe.engine for probe in report.probes} == {"ekcp", "ekre", "ekie"}
