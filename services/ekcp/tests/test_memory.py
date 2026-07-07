"""Tests for the memory framework: store, retrieve, compress, retain, route."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from config.settings import MemorySettings
from domain.intent import IntentScope, RoutingTarget
from domain.memory import (
    CompressionLevel,
    InMemoryMemoryStore,
    MemoryError,
    MemoryFramework,
    MemoryPolicy,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    ValidationMethod,
    route_for_scope,
)


class _Clock:
    """Manually advanced clock for deterministic retention tests."""

    def __init__(self) -> None:
        self._now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


def _framework(
    clock: Callable[[], datetime] | None = None, **overrides: object
) -> MemoryFramework:
    settings = MemorySettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return MemoryFramework(
        InMemoryMemoryStore(), MemoryPolicy.from_settings(settings), clock=clock
    )


def test_remember_sets_confidence_and_expiry() -> None:
    framework = _framework()
    item = framework.remember(
        tenant_id="tenant-a",
        content="User prefers concise answers",
        memory_type=MemoryType.PREFERENCE,
        scope=MemoryScope.USER,
        validation_method=ValidationMethod.USER_CONFIRMED,
    )
    assert item.confidence == 0.95
    assert item.expires_at is not None
    assert item.status is MemoryStatus.ACTIVE


def test_organizational_scope_never_expires() -> None:
    framework = _framework()
    item = framework.remember(
        tenant_id="tenant-a",
        content="Company was founded in 2001",
        memory_type=MemoryType.FACT,
        scope=MemoryScope.ORGANIZATIONAL,
        validation_method=ValidationMethod.KNOWLEDGE_RETRIEVED,
    )
    assert item.expires_at is None


def test_recall_ranks_by_relevance() -> None:
    framework = _framework()
    for content, topic in (
        ("User prefers JSON responses", "response_format"),
        ("Meeting scheduled for Friday", "calendar"),
    ):
        framework.remember(
            tenant_id="tenant-a",
            content=content,
            memory_type=MemoryType.PREFERENCE,
            scope=MemoryScope.USER,
            validation_method=ValidationMethod.USER_CONFIRMED,
            topic=topic,
        )
    hits = framework.recall(tenant_id="tenant-a", query="JSON responses preference")
    assert hits
    assert "JSON" in hits[0].item.content
    assert hits[0].item.retrieval_count == 1


def test_recall_filters_below_min_confidence() -> None:
    framework = _framework()
    framework.remember(
        tenant_id="tenant-a",
        content="Weak inference about the user",
        memory_type=MemoryType.INSIGHT,
        scope=MemoryScope.USER,
        validation_method=ValidationMethod.LLM_INFERRED,
    )
    hits = framework.recall(tenant_id="tenant-a", query="user", min_confidence=0.8)
    assert hits == []


def test_recall_as_context_items() -> None:
    framework = _framework()
    framework.remember(
        tenant_id="tenant-a",
        content="User prefers dark mode",
        memory_type=MemoryType.PREFERENCE,
        scope=MemoryScope.USER,
        validation_method=ValidationMethod.USER_CONFIRMED,
        topic="ui",
    )
    items = framework.recall_as_context(tenant_id="tenant-a", query="user prefers")
    assert items
    assert items[0].source.value == "memory"


def test_consolidate_summarizes_and_archives_sources() -> None:
    framework = _framework()
    for content in ("Decided to launch in Q3", "Budget approved at 50k"):
        framework.remember(
            tenant_id="tenant-a",
            content=content,
            memory_type=MemoryType.DECISION,
            scope=MemoryScope.CONVERSATION,
            validation_method=ValidationMethod.USER_CONFIRMED,
            conversation_id="conv-1",
            topic="planning",
        )
    consolidated = framework.consolidate(
        tenant_id="tenant-a", conversation_id="conv-1", level=CompressionLevel.SUMMARY
    )
    assert consolidated.memory_type is MemoryType.INSIGHT
    assert len(consolidated.related_memories) == 2
    assert "Summary of 2 memories" in consolidated.content


def test_consolidate_abstract_level() -> None:
    framework = _framework()
    framework.remember(
        tenant_id="tenant-a",
        content="Chose vendor X",
        memory_type=MemoryType.DECISION,
        scope=MemoryScope.CONVERSATION,
        validation_method=ValidationMethod.USER_CONFIRMED,
        conversation_id="conv-1",
        topic="procurement",
    )
    consolidated = framework.consolidate(
        tenant_id="tenant-a", conversation_id="conv-1", level=CompressionLevel.ABSTRACT
    )
    assert consolidated.content.startswith("Consolidated 1 memories")


def test_consolidate_without_memories_raises() -> None:
    framework = _framework()
    with pytest.raises(MemoryError):
        framework.consolidate(tenant_id="tenant-a", conversation_id="missing")


def test_expire_marks_aged_memories() -> None:
    clock = _Clock()
    framework = _framework(clock, working_ttl_seconds=60.0)
    item = framework.remember(
        tenant_id="tenant-a",
        content="temp reasoning",
        memory_type=MemoryType.FACT,
        scope=MemoryScope.WORKING,
        validation_method=ValidationMethod.AGENT_GENERATED,
    )
    clock.advance(120.0)
    expired = framework.expire(tenant_id="tenant-a")
    assert expired == 1
    assert framework.get("tenant-a", item.memory_id).status is MemoryStatus.EXPIRED


def test_forget_hard_deletes_user_memories() -> None:
    framework = _framework()
    item = framework.remember(
        tenant_id="tenant-a",
        content="User personal note",
        memory_type=MemoryType.FACT,
        scope=MemoryScope.USER,
        validation_method=ValidationMethod.USER_CONFIRMED,
        user_id="analyst-1",
    )
    deleted = framework.forget(tenant_id="tenant-a", user_id="analyst-1")
    assert deleted == 1
    with pytest.raises(MemoryError):
        framework.get("tenant-a", item.memory_id)


def test_route_for_scope() -> None:
    assert route_for_scope(IntentScope.PERSONAL).primary_target is RoutingTarget.MEMORY
    assert route_for_scope(IntentScope.PERSONAL).use_memory is True
    assert route_for_scope(IntentScope.ORGANIZATIONAL).use_knowledge is True
    mixed = route_for_scope(IntentScope.MIXED)
    assert mixed.use_memory and mixed.use_knowledge
