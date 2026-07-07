"""Offline demo of the EKCP S1 conversation core loop.

Runs fully offline (no server, no network). Demonstrates the Conversation
Digital Twin lifecycle, session management, and the intent-before-execution gate
routing personal versus organizational messages and requesting clarification on
ambiguous input.
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
    build_conversation_engine,
    build_conversation_manager,
    build_conversation_store,
    build_event_sink,
    build_session_manager,
    build_session_store,
    configure_observability,
)
from config.settings import EkcpSettings  # noqa: E402


def main() -> None:
    """Exercise the S1 conversation core loop, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)

    store = build_conversation_store(settings)
    sink = build_event_sink(settings)
    manager = build_conversation_manager(settings, store, event_sink=sink)
    sessions = build_session_manager(settings, build_session_store(settings))
    engine = build_conversation_engine(settings, store, event_sink=sink)

    session = sessions.create(tenant_id="tenant-a", user_id="analyst-1")
    conversation = manager.create(
        tenant_id="tenant-a",
        owner_id="analyst-1",
        title="Support",
        session_id=session.session_id,
    )
    print("Started conversation:", conversation.conversation_id, conversation.current_state)

    for message in (
        "What is the company policy on remote work?",
        "What did we discuss yesterday about my preferences?",
        "hmm",
    ):
        result = engine.handle_interaction(
            "tenant-a", conversation.conversation_id, message=message
        )
        classification = result.decision.classification
        print(
            f"- msg={message!r} -> intent={classification.intent} "
            f"scope={classification.scope} route={result.decision.routing_target} "
            f"state={result.conversation.current_state} "
            f"clarify={classification.requires_clarification}"
        )

    final = manager.get("tenant-a", conversation.conversation_id)
    print("Interaction count:", final.metrics.interaction_count)
    print("Human interventions:", final.metrics.human_intervention_count)
    print("Events emitted:", len(sink.history()) if hasattr(sink, "history") else "logging")


if __name__ == "__main__":
    main()
