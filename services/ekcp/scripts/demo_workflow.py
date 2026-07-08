"""Offline demo of the EKCP S7 workflow, events, and knowledge integration.

Runs fully offline (no server, no network). Demonstrates triggering a workflow
(decomposed into a plan) with platform events, and resilient EKRE knowledge
retrieval degrading gracefully to local context when EKRE is disabled/unavailable.
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
    build_event_bus,
    build_knowledge_retriever,
    build_workflow_orchestrator,
    configure_observability,
)
from config.settings import EkcpSettings  # noqa: E402
from domain.workflow import InMemoryEventBus  # noqa: E402


def main() -> None:
    """Exercise the S7 workflow and knowledge integration, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)
    bus = build_event_bus(settings)
    orchestrator = build_workflow_orchestrator(settings, event_bus=bus)
    knowledge = build_knowledge_retriever(settings)

    print("--- workflow trigger ---")
    workflow = orchestrator.trigger(
        tenant_id="tenant-a",
        objective="retrieve sales data, generate report, obtain approval, notify stakeholders",
    )
    print(
        f"  workflow={workflow.workflow_id} state={workflow.state} "
        f"plan={workflow.plan_id} tasks={workflow.task_count}"
    )
    paused = orchestrator.pause("tenant-a", workflow.workflow_id)
    resumed = orchestrator.resume("tenant-a", workflow.workflow_id)
    print(f"  paused -> {paused.state}; resumed -> {resumed.state}")

    print("--- platform events ---")
    if isinstance(bus, InMemoryEventBus):
        for event in bus.history():
            print(f"  {event.event_type} payload={event.payload}")

    print("--- knowledge retrieval (EKRE disabled -> graceful degradation) ---")
    result = knowledge.retrieve(
        "What is the remote work policy?",
        tenant_id="tenant-a",
        security_context={
            "user_id": "analyst-1",
            "tenant_id": "tenant-a",
            "classification_clearance": "internal",
        },
    )
    print(f"  degraded={result.degraded} reason={result.reason!r}")
    print("  session continues using local context (memory + conversation history)")


if __name__ == "__main__":
    main()
