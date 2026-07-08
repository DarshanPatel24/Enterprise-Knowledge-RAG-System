"""Offline demo of the EKCP S8 deployment and master handoff readiness.

Runs fully offline (no server, no network). Demonstrates the deployment readiness
assessment, multi-tenant isolation posture, the per-tenant concurrency limiter,
and the master integration handoff package with proven KPIs.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path so `src/` packages import when run as a script.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from composition import (  # noqa: E402
    build_deployment_readiness,
    build_master_handoff_package,
    build_multi_tenant_readiness,
    build_tenant_limiter,
    configure_observability,
)
from config.settings import EkcpSettings  # noqa: E402
from domain.readiness import ReadinessReport  # noqa: E402


def _print_report(report: ReadinessReport) -> None:
    print(f"--- {report.name} readiness: {'READY' if report.ready else 'NOT READY'} ---")
    for finding in report.findings:
        print(f"  [{finding.severity.value:<7}] {finding.check}: {finding.message}")


def main() -> None:
    """Exercise the S8 deployment and master handoff readiness, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)

    _print_report(build_deployment_readiness(settings))
    _print_report(build_multi_tenant_readiness(settings))

    print("--- per-tenant admission control ---")
    limiter = build_tenant_limiter(settings)
    admitted = sum(limiter.acquire("tenant-a") for _ in range(12))
    print(f"  admitted {admitted} of 12 concurrent requests for tenant-a")

    package = build_master_handoff_package(settings)
    print(f"--- master handoff: {'READY' if package.ready else 'NOT READY'} ---")
    print(f"  service: {package.service} v{package.version}")
    print(f"  endpoints: {len(package.endpoints)}")
    print(f"  contracts: {', '.join(package.contracts)}")
    print(f"  policy enforcement coverage: {package.policy_enforcement_coverage}")
    print(f"  audit coverage: {package.audit_coverage}")


if __name__ == "__main__":
    main()
