"""Offline demo of the EKCP S4 memory framework.

Runs fully offline (no server, no network). Demonstrates remembering governed
memories with per-scope retention, ranked recall, consolidation into a long-term
summary, personal versus organizational routing, and right-to-be-forgotten.
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

from composition import build_memory_framework, configure_observability  # noqa: E402
from config.settings import EkcpSettings  # noqa: E402
from domain.intent import IntentScope  # noqa: E402
from domain.memory import (  # noqa: E402
    CompressionLevel,
    MemoryScope,
    MemoryType,
    ValidationMethod,
    route_for_scope,
)


def main() -> None:
    """Exercise the S4 memory framework, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)
    memory = build_memory_framework(settings)

    memory.remember(
        tenant_id="tenant-a",
        content="User prefers concise JSON answers",
        memory_type=MemoryType.PREFERENCE,
        scope=MemoryScope.USER,
        validation_method=ValidationMethod.USER_CONFIRMED,
        topic="response_format",
        user_id="analyst-1",
    )
    memory.remember(
        tenant_id="tenant-a",
        content="Decided to launch the pilot in Q3",
        memory_type=MemoryType.DECISION,
        scope=MemoryScope.CONVERSATION,
        validation_method=ValidationMethod.USER_CONFIRMED,
        conversation_id="conv-1",
        topic="planning",
        user_id="analyst-1",
    )

    print("--- recall: 'JSON answer preference' ---")
    for hit in memory.recall(tenant_id="tenant-a", query="JSON answer preference"):
        print(f"  score={hit.score:.3f} [{hit.item.scope}] {hit.item.content}")

    print("--- routing ---")
    for scope in (IntentScope.PERSONAL, IntentScope.ORGANIZATIONAL, IntentScope.MIXED):
        decision = route_for_scope(scope)
        print(
            f"  {scope}: memory={decision.use_memory} "
            f"knowledge={decision.use_knowledge} primary={decision.primary_target}"
        )

    print("--- consolidate conversation ---")
    memory.remember(
        tenant_id="tenant-a",
        content="Budget approved at 50k",
        memory_type=MemoryType.DECISION,
        scope=MemoryScope.CONVERSATION,
        validation_method=ValidationMethod.USER_CONFIRMED,
        conversation_id="conv-1",
        topic="planning",
    )
    consolidated = memory.consolidate(
        tenant_id="tenant-a", conversation_id="conv-1", level=CompressionLevel.SUMMARY
    )
    print(f"  consolidated ({len(consolidated.related_memories)} sources): {consolidated.content}")

    print("--- forget (right-to-be-forgotten) ---")
    deleted = memory.forget(tenant_id="tenant-a", user_id="analyst-1")
    print(f"  deleted {deleted} memories for analyst-1")


if __name__ == "__main__":
    main()
