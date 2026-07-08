"""Consolidated operational readiness across the engines (SLO/SLA evidence).

Aggregates each engine's readiness surface into one report. EKRE and EKCP expose
``/v1/readiness`` (a structured report with a ``ready`` flag); EKIE exposes
``/health/ready``. A target is ready when it answers HTTP 200 and does not report
``ready: false``.
"""

from __future__ import annotations

from dataclasses import dataclass

from harness import clients


@dataclass(frozen=True)
class ReadinessTarget:
    """An engine readiness endpoint to probe."""

    engine: str
    base_url: str
    path: str


@dataclass(frozen=True)
class ReadinessProbe:
    """The outcome of probing one engine's readiness endpoint."""

    engine: str
    url: str
    status_code: int
    ready: bool
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    """The consolidated readiness of the platform."""

    probes: list[ReadinessProbe]

    @property
    def all_ready(self) -> bool:
        return all(probe.ready for probe in self.probes)


def probe_readiness(target: ReadinessTarget) -> ReadinessProbe:
    """Probe one engine's readiness endpoint and normalise the result."""
    try:
        response = clients.get(target.base_url, target.path)
    except Exception as exc:
        return ReadinessProbe(target.engine, f"{target.base_url}{target.path}", 0, False, str(exc))

    ready = False
    detail = ""
    if response.status_code == 200:
        try:
            body = response.json()
            ready = body.get("ready", True) is not False
            detail = str(body.get("status", body.get("ready", "ok")))
        except ValueError:
            ready = True
            detail = "non-json 200"
    else:
        detail = f"HTTP {response.status_code}"
    return ReadinessProbe(
        target.engine, f"{target.base_url}{target.path}", response.status_code, ready, detail
    )


def aggregate_readiness(targets: list[ReadinessTarget]) -> ReadinessReport:
    """Probe every target and build the consolidated report."""
    return ReadinessReport([probe_readiness(target) for target in targets])


def render_markdown(report: ReadinessReport) -> str:
    """Render the readiness report as Markdown evidence."""
    lines = [
        "# M2-S3 Consolidated Readiness Report",
        "",
        f"Overall ready: {'YES' if report.all_ready else 'NO'}",
        "",
        "| Engine | Endpoint | Status | Ready | Detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for probe in report.probes:
        lines.append(
            f"| {probe.engine} | {probe.url} | {probe.status_code} | "
            f"{'yes' if probe.ready else 'NO'} | {probe.detail} |"
        )
    return "\n".join(lines) + "\n"
