"""Classification ranking and monotonic downgrade prevention (handbook 12).

Reuses the shared :class:`ClassificationClearance` contract. Clearance covers a
resource when the principal's rank is at least the resource's rank; classification
propagation is monotonic unless a downgrade is explicitly permitted by policy.
"""

from __future__ import annotations

from contracts.enums import ClassificationClearance
from domain.governance.errors import GovernanceError, GovernanceErrorType

_ORDER: tuple[str, ...] = ("public", "internal", "confidential", "restricted")


def rank(clearance: ClassificationClearance) -> int:
    """Return the sensitivity rank (higher means more restrictive)."""
    return _ORDER.index(clearance.value)


def is_cleared(
    principal_clearance: ClassificationClearance, resource: ClassificationClearance
) -> bool:
    """Return whether a principal clearance covers a resource classification."""
    return rank(principal_clearance) >= rank(resource)


def is_downgrade(
    source: ClassificationClearance, target: ClassificationClearance
) -> bool:
    """Return whether ``target`` is less restrictive than ``source``."""
    return rank(target) < rank(source)


def ensure_no_downgrade(
    source: ClassificationClearance,
    target: ClassificationClearance,
    *,
    allow_downgrade: bool = False,
) -> ClassificationClearance:
    """Enforce monotonic classification propagation, returning the target level."""
    if allow_downgrade or not is_downgrade(source, target):
        return target
    raise GovernanceError(
        GovernanceErrorType.CLEARANCE_VIOLATION,
        (
            f"classification downgrade from {source.value!r} to "
            f"{target.value!r} is not permitted"
        ),
    )


def parse_clearance(value: str) -> ClassificationClearance:
    """Parse a clearance string, raising ``UNKNOWN_CLASSIFICATION`` when invalid."""
    try:
        return ClassificationClearance(value)
    except ValueError as exc:
        raise GovernanceError(
            GovernanceErrorType.UNKNOWN_CLASSIFICATION,
            f"unknown classification clearance {value!r}",
        ) from exc
