"""EKRE handoff readiness package (EKIE-S9-5).

Assembles the immutable descriptor EKRE needs to consume a published document:
collection coordinates, embedding model identity, vector geometry, governance
classification, and the source content hash for provenance. The package is only
considered ready when end-to-end validation passes, guaranteeing EKRE receives a
complete and lineage-intact vector set.
"""

from __future__ import annotations

from pydantic import BaseModel

from domain.control_plane import ControlPlaneDatabase, Document
from domain.orchestration.engine import WorkflowResult
from domain.storage import AssetStorage
from domain.validation.assets import lineage_relations, load_pipeline_assets
from domain.validation.errors import ValidationError, ValidationErrorType
from domain.validation.pipeline import PipelineValidator


class HandoffPackage(BaseModel):
    """Immutable handoff descriptor consumed by EKRE for a published document."""

    model_config = {"frozen": True}

    document_id: str
    tenant_id: str
    collection: str
    provider: str
    model_name: str
    dimension: int
    distance_metric: str
    vector_count: int
    chunk_count: int
    classification_clearance: str
    source_content_hash: str
    lineage_relations: tuple[str, ...]
    validation_passed: bool


def build_handoff_package(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    result: WorkflowResult,
) -> HandoffPackage:
    """Build the EKRE handoff package for a completed workflow result."""
    assets = load_pipeline_assets(
        db,
        storage,
        document_id=result.document_id,
        tenant_id=result.tenant_id,
    )
    if assets.vectors is None:
        raise ValidationError(
            ValidationErrorType.NOT_PUBLISHED,
            f"document {result.document_id!r} has no published vector asset",
        )
    if assets.chunks is None or assets.embedding is None:
        raise ValidationError(
            ValidationErrorType.MISSING_ASSET,
            f"document {result.document_id!r} is missing chunk or embedding assets",
        )

    with db.session() as session:
        document = session.get(Document, result.document_id)
        if document is None or document.tenant_id != result.tenant_id:
            raise ValidationError(
                ValidationErrorType.MISSING_ASSET,
                f"document {result.document_id!r} not found for tenant "
                f"{result.tenant_id!r}",
            )
        classification = document.classification_clearance
        content_hash = document.content_hash

    validation = PipelineValidator(db, storage).validate(result)
    return HandoffPackage(
        document_id=result.document_id,
        tenant_id=result.tenant_id,
        collection=assets.vectors.collection,
        provider=assets.vectors.provider,
        model_name=assets.vectors.model_name,
        dimension=assets.vectors.dimension,
        distance_metric=assets.vectors.distance_metric.value,
        vector_count=assets.vectors.vector_count,
        chunk_count=assets.chunks.chunk_count,
        classification_clearance=classification,
        source_content_hash=content_hash,
        lineage_relations=tuple(sorted(lineage_relations(db, result.document_id))),
        validation_passed=validation.passed,
    )
