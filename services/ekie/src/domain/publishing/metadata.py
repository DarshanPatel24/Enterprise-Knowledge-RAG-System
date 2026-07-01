"""Metadata mapping and the required-field validation gate (handbook 11.12).

Every published vector must carry complete mandatory governance metadata before
it reaches the vector database. This module builds the metadata and exposes the
validation gate enforced by the publishing engine (EKIE-S6-4).
"""

from __future__ import annotations

from domain.publishing.models import VectorMetadata

# Mandatory metadata fields that must be present and non-empty before publishing.
MANDATORY_METADATA_FIELDS: tuple[str, ...] = (
    "document_id",
    "chunk_id",
    "tenant_id",
    "classification_clearance",
    "distance_metric",
    "collection",
    "embedding_model",
)


def missing_required_fields(metadata: VectorMetadata) -> list[str]:
    """Return the names of mandatory metadata fields that are empty.

    Integer fields (``embedding_version``, ``dimension``) are validated for
    positivity so a published vector always declares a real model version and
    dimensionality.
    """
    missing = [
        field
        for field in MANDATORY_METADATA_FIELDS
        if not str(getattr(metadata, field)).strip()
    ]
    if metadata.embedding_version <= 0:
        missing.append("embedding_version")
    if metadata.dimension <= 0:
        missing.append("dimension")
    return missing
