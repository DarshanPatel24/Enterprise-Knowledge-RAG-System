"""Pipeline-level end-to-end validation (handbook Chapter 20, EKIE-S9-1).

Aggregates the per-facet validators into a single report for a completed
document ingestion, reading assets back from the same Control Plane and object
storage the pipeline wrote to. A failing sub-check surfaces as an error finding
without aborting the remaining checks, giving a full picture of pipeline health.
"""

from __future__ import annotations

from domain.control_plane import ControlPlaneDatabase
from domain.orchestration.engine import WorkflowResult
from domain.storage import AssetStorage
from domain.validation.assets import load_pipeline_assets
from domain.validation.report import ValidationReport, error
from domain.validation.validators import (
    validate_chunks,
    validate_embeddings,
    validate_lineage,
    validate_vectors,
    validate_workflow,
)


class PipelineValidator:
    """Runs the full end-to-end validation suite for one document."""

    def __init__(self, db: ControlPlaneDatabase, storage: AssetStorage) -> None:
        self._db = db
        self._storage = storage

    def validate(self, result: WorkflowResult) -> ValidationReport:
        """Validate a completed workflow result end to end."""
        reports = [
            validate_workflow(result),
            validate_lineage(self._db, document_id=result.document_id),
        ]
        assets = load_pipeline_assets(
            self._db,
            self._storage,
            document_id=result.document_id,
            tenant_id=result.tenant_id,
        )
        if assets.chunks is None:
            reports.append(
                ValidationReport(
                    name="chunks",
                    findings=(error("chunks", "chunk asset could not be loaded"),),
                )
            )
        else:
            reports.append(validate_chunks(assets.chunks))

        if assets.chunks is not None and assets.embedding is not None:
            reports.append(validate_embeddings(assets.chunks, assets.embedding))
        elif assets.embedding is None:
            reports.append(
                ValidationReport(
                    name="embeddings",
                    findings=(
                        error("embeddings", "embedding asset could not be loaded"),
                    ),
                )
            )

        if assets.embedding is not None and assets.vectors is not None:
            reports.append(validate_vectors(assets.embedding, assets.vectors))
        elif assets.vectors is None:
            reports.append(
                ValidationReport(
                    name="vectors",
                    findings=(error("vectors", "vector asset could not be loaded"),),
                )
            )

        return ValidationReport.merge(
            f"pipeline:{result.document_id}", reports
        )
