"""Offline demo of the EKCP S6 governance, security, and policy framework.

Runs fully offline (no server, no network). Demonstrates RBAC + ABAC policy
enforcement with audit, PII masking of an outbound response, and security
context propagation to EKRE with monotonic classification.
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

from composition import build_governance_guard, configure_observability  # noqa: E402
from config.settings import EkcpSettings  # noqa: E402
from contracts.enums import ClassificationClearance  # noqa: E402
from domain.governance import (  # noqa: E402
    GovernanceError,
    InMemoryAuditSink,
    Permission,
    Principal,
    Role,
)


def main() -> None:
    """Exercise the S6 governance framework, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)
    guard = build_governance_guard(settings)

    power_user = Principal(
        user_id="analyst-1",
        tenant_id="tenant-a",
        roles=frozenset({Role.POWER_USER}),
        clearance=ClassificationClearance.CONFIDENTIAL,
    )
    plain_user = Principal(
        user_id="intern-9",
        tenant_id="tenant-a",
        roles=frozenset({Role.USER}),
        clearance=ClassificationClearance.INTERNAL,
    )

    print("--- policy enforcement ---")
    decision = guard.authorize(power_user, Permission.INVOKE_AGENT, "research-agent")
    print(f"  power_user invoke_agent -> allowed={decision.allowed}")
    try:
        guard.authorize(plain_user, Permission.INVOKE_AGENT, "research-agent")
    except GovernanceError as exc:
        print(f"  user invoke_agent -> denied ({exc.error_type})")

    print("--- PII masking ---")
    masked, count = guard.mask_response(
        "Reach me at jane@acme.com or 555-123-4567",
        actor="analyst-1",
        tenant_id="tenant-a",
    )
    print(f"  masked={masked!r} redactions={count}")

    print("--- security context propagation to EKRE ---")
    payload = guard.propagate_security_context(power_user)
    print(f"  payload={payload}")

    print("--- audit trail ---")
    sink = guard.audit_sink
    if isinstance(sink, InMemoryAuditSink):
        for record in sink.history():
            print(f"  {record.action} [{record.result}] resource={record.resource}")


if __name__ == "__main__":
    main()
