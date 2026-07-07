"""Offline demo of the EKCP S0 foundations: config, security gate, observability.

Runs fully offline (no server, no network). Demonstrates the security context
ingress gate, the structured logging + correlation scope, the latency baseline,
and the SSE chat event schema the Web UI consumes.
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

from api.chat import format_sse_event  # noqa: E402
from composition import build_security_validator, configure_observability  # noqa: E402
from config.settings import EkcpSettings  # noqa: E402
from domain.observability import (  # noqa: E402
    LatencyRecorder,
    correlation_scope,
    get_logger,
)
from domain.security import SecurityError  # noqa: E402


def main() -> None:
    """Exercise the S0 foundations end to end, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)
    logger = get_logger("ekcp.demo.foundations")
    validator = build_security_validator(settings)

    with correlation_scope(
        tenant_id="tenant-a", correlation_id="corr-1", session_id="sess-1"
    ):
        recorder = LatencyRecorder()
        with recorder.stage("security_gate"):
            context = validator.validate(
                {
                    "user_id": "analyst-1",
                    "tenant_id": "tenant-a",
                    "classification_clearance": "internal",
                },
                expected_tenant_id="tenant-a",
            )
        logger.info("security_context_validated", extra={"user_id": context.user_id})

        try:
            validator.validate(
                {
                    "user_id": "intruder",
                    "tenant_id": "tenant-b",
                    "classification_clearance": "internal",
                },
                expected_tenant_id="tenant-a",
            )
        except SecurityError as exc:
            logger.warning("security_denied", extra={"error_type": exc.error_type})

        print("Security context:", context.user_id, context.classification_clearance)
        print("Latency breakdown:", recorder.breakdown().stages)
        print("--- SSE chat event schema (echo stub) ---")
        for token in "governed conversation online".split():
            print(format_sse_event("token", {"text": token}), end="")
        print(
            format_sse_event(
                "done",
                {"session_id": "sess-1", "correlation_id": "corr-1", "finish_reason": "stop"},
            ),
            end="",
        )


if __name__ == "__main__":
    main()
