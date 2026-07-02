"""Data classification levels and monotonic propagation (handbook 17.7).

Classification flows Document -> Markdown -> Chunks -> Embeddings -> Vectors.
No downgrade is allowed unless configuration explicitly permits it, guaranteeing
a published asset never carries a weaker clearance than its source document.
"""

from __future__ import annotations

from enum import StrEnum

from domain.security.errors import SecurityError, SecurityErrorType

# Ordered from least to most restrictive; index is the sensitivity rank.
_ORDER: tuple[str, ...] = (
    "public",
    "internal",
    "confidential",
    "highly_confidential",
    "restricted",
)


class Classification(StrEnum):
    """Enterprise data classification levels (handbook 17.7)."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"
    RESTRICTED = "restricted"


def parse_classification(value: str) -> Classification:
    """Return the :class:`Classification` for ``value`` (case-insensitive)."""
    normalized = value.strip().lower()
    try:
        return Classification(normalized)
    except ValueError as exc:
        raise SecurityError(
            SecurityErrorType.UNKNOWN_CLASSIFICATION,
            f"Unknown classification level: {value!r}",
        ) from exc


def rank(classification: Classification) -> int:
    """Return the sensitivity rank (higher means more restrictive)."""
    return _ORDER.index(classification.value)


def is_downgrade(source: Classification, target: Classification) -> bool:
    """Return ``True`` when ``target`` is less restrictive than ``source``."""
    return rank(target) < rank(source)


def ensure_no_downgrade(
    source: Classification,
    target: Classification,
    *,
    allow_downgrade: bool = False,
) -> Classification:
    """Enforce monotonic classification propagation.

    Returns ``target`` when the transition is permitted. Raises
    :class:`SecurityError` when ``target`` weakens ``source`` and downgrades are
    not explicitly permitted.
    """
    if allow_downgrade or not is_downgrade(source, target):
        return target
    raise SecurityError(
        SecurityErrorType.CLEARANCE_VIOLATION,
        f"Classification downgrade from {source.value!r} to {target.value!r} "
        "is not permitted",
    )


def is_cleared(principal_clearance: Classification, resource: Classification) -> bool:
    """Return ``True`` when a principal clearance covers a resource level."""
    return rank(principal_clearance) >= rank(resource)
