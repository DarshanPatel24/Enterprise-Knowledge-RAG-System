"""Memory compression and consolidation (handbook 8.16).

Compresses a set of active memories into a single long-term memory via
deterministic summarization or abstraction, and consolidates duplicates by
merging items with identical normalized content. No model is required; the
compression is character-based and reproducible offline.
"""

from __future__ import annotations

from collections.abc import Sequence

from domain.memory.models import CompressionLevel, MemoryItem

_MAX_SUMMARY_FRAGMENT_CHARS = 160


def _first_sentence(text: str) -> str:
    stripped = text.strip()
    for terminator in (". ", "\n"):
        index = stripped.find(terminator)
        if index != -1:
            stripped = stripped[:index]
            break
    return stripped[:_MAX_SUMMARY_FRAGMENT_CHARS].strip()


def consolidate_duplicates(
    items: Sequence[MemoryItem],
) -> tuple[list[MemoryItem], int]:
    """Merge memories with identical normalized content, keeping the highest confidence."""
    best: dict[str, MemoryItem] = {}
    merged = 0
    for item in items:
        key = item.content.strip().lower()
        existing = best.get(key)
        if existing is None:
            best[key] = item
            continue
        merged += 1
        winner = existing if existing.confidence >= item.confidence else item
        related = tuple(
            dict.fromkeys((*existing.related_memories, *item.related_memories))
        )
        best[key] = winner.model_copy(update={"related_memories": related})
    return list(best.values()), merged


def summarize(items: Sequence[MemoryItem], *, level: CompressionLevel) -> str:
    """Return a deterministic summary of the memories at the given level."""
    if not items:
        return ""
    topics = sorted({item.topic for item in items if item.topic})
    topic_label = ", ".join(topics) if topics else "general"
    if level is CompressionLevel.ABSTRACT:
        return f"Consolidated {len(items)} memories on {topic_label}."
    fragments = [_first_sentence(item.content) for item in items]
    fragments = [fragment for fragment in fragments if fragment]
    joined = "; ".join(fragments)
    return f"Summary of {len(items)} memories on {topic_label}: {joined}"
