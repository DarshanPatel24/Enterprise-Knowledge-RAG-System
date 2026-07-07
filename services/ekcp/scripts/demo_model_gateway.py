"""Offline demo of the EKCP S3 model management and LLM gateway.

Runs fully offline (no server, no network) using the deterministic echo model.
Demonstrates the governed Model Invocation Contract (routing, token accounting,
cost estimate) and streaming through the gateway.
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

from composition import build_model_gateway, configure_observability  # noqa: E402
from config.settings import EkcpSettings  # noqa: E402
from domain.gateway import GenerationRequest, StreamEventType  # noqa: E402


def main() -> None:
    """Exercise the S3 model gateway, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)
    gateway = build_model_gateway(settings)

    request = GenerationRequest(
        prompt_text=(
            "System: You are the enterprise assistant.\n"
            "Relevant context:\n- (enterprise) Remote work is allowed two days per week.\n"
            "User request: What is our remote work policy?"
        ),
        tenant_id="tenant-a",
    )

    response = gateway.invoke(request)
    print("Model:", response.model_id, "provider:", response.provider)
    print("Output:", response.output_text)
    print(
        "Tokens:",
        response.token_usage.total_tokens,
        "cost:",
        response.cost_estimate,
        "latency_ms:",
        response.latency_ms,
    )
    print("Tenant ledger tokens:", gateway.ledger.tokens_for("tenant-a"))

    print("--- streaming ---")
    for event in gateway.stream(request):
        if event.event_type is StreamEventType.TOKEN:
            print(event.text, end="")
        elif event.event_type is StreamEventType.DONE:
            usage = event.token_usage
            print(
                f"\n[done] tokens={usage.total_tokens if usage else 0} "
                f"cost={event.cost_estimate}"
            )


if __name__ == "__main__":
    main()
