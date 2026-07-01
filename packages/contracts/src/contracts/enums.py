"""Shared enumerations for cross-engine contracts."""

from enum import StrEnum


class DistanceMetric(StrEnum):
    """Vector distance metric declared by EKIE and inherited by EKRE."""

    COSINE = "cosine"
    DOT_PRODUCT = "dot_product"
    EUCLIDEAN = "euclidean"


class ClassificationClearance(StrEnum):
    """Enterprise classification clearance levels for access control."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
