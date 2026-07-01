"""Shared cross-engine contracts for EK-RAG (EKIE, EKRE, EKCP)."""

from contracts.base import VersionedContract
from contracts.enums import ClassificationClearance, DistanceMetric
from contracts.events import EnterpriseDataPurgeEvent
from contracts.execution_context import ExecutionContext
from contracts.retrieval import (
    Citation,
    RetrievalCandidate,
    RetrievalContextPackage,
)
from contracts.security_context import SecurityContext
from contracts.vector_schema import VectorCollectionRecord
from contracts.version import (
    CONTRACTS_VERSION,
    MIN_SUPPORTED_CONTRACTS_VERSION,
)

__all__ = [
    "CONTRACTS_VERSION",
    "MIN_SUPPORTED_CONTRACTS_VERSION",
    "VersionedContract",
    "ClassificationClearance",
    "DistanceMetric",
    "ExecutionContext",
    "SecurityContext",
    "VectorCollectionRecord",
    "Citation",
    "RetrievalCandidate",
    "RetrievalContextPackage",
    "EnterpriseDataPurgeEvent",
]
