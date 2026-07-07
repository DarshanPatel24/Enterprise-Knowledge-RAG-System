"""Pre-pool security filtering (handbook Chapter 29).

Authorization is enforced *before* candidates are collected: the set of
clearances a principal may see is computed from the security context and pushed
into the repository connector, so unauthorized documents never leave the
repository. A post-retrieval safety net drops anything that slips through.
"""

from __future__ import annotations

from collections.abc import Sequence

from contracts.enums import ClassificationClearance
from contracts.security_context import SecurityContext
from domain.connectors.base import RepositoryDocument
from domain.retrieval.errors import RetrievalWorkerError, RetrievalWorkerErrorType

# Ascending clearance order; a principal may see everything at or below its level.
_ORDER: tuple[ClassificationClearance, ...] = (
    ClassificationClearance.PUBLIC,
    ClassificationClearance.INTERNAL,
    ClassificationClearance.CONFIDENTIAL,
    ClassificationClearance.RESTRICTED,
)


def resolve_allowed_clearances(
    security_context: SecurityContext | None, *, require_security_context: bool
) -> tuple[str, ...]:
    """Return the clearance values a principal is authorized to retrieve.

    Raises :class:`RetrievalWorkerError` when a context is required but absent.
    With no context and none required, only public documents are authorized.
    """
    if security_context is None:
        if require_security_context:
            raise RetrievalWorkerError(
                RetrievalWorkerErrorType.UNAUTHORIZED,
                "a security context is required to retrieve candidates",
            )
        return (ClassificationClearance.PUBLIC.value,)
    index = _ORDER.index(security_context.classification_clearance)
    return tuple(clearance.value for clearance in _ORDER[: index + 1])


def enforce_clearance(
    documents: Sequence[RepositoryDocument], allowed: Sequence[str]
) -> list[RepositoryDocument]:
    """Drop any document whose classification is not within ``allowed``.

    Defense in depth: the connector already filters at the data boundary; this
    guarantees no unauthorized candidate can enter the pool even if a connector
    misbehaves.
    """
    allowed_set = set(allowed)
    return [doc for doc in documents if doc.classification_clearance in allowed_set]
