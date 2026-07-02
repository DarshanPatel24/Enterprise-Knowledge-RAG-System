"""Pipeline validation, load testing, and EKRE handoff readiness (Chapter 20)."""

from __future__ import annotations

from domain.validation.assets import (
    PipelineAssets,
    lineage_relations,
    load_chunks,
    load_embedding,
    load_pipeline_assets,
    load_vectors,
    present_asset_types,
)
from domain.validation.errors import ValidationError, ValidationErrorType
from domain.validation.failure import InjectedStageFailure, failing_stages
from domain.validation.handoff import HandoffPackage, build_handoff_package
from domain.validation.load import (
    DocumentLoadSpec,
    LoadReport,
    run_load,
)
from domain.validation.pipeline import PipelineValidator
from domain.validation.readiness import assess_readiness
from domain.validation.report import (
    Severity,
    ValidationFinding,
    ValidationReport,
    error,
    finding,
    info,
    warning,
)
from domain.validation.validators import (
    validate_chunks,
    validate_embeddings,
    validate_lineage,
    validate_vectors,
    validate_workflow,
)

__all__ = [
    "DocumentLoadSpec",
    "HandoffPackage",
    "InjectedStageFailure",
    "LoadReport",
    "PipelineAssets",
    "PipelineValidator",
    "Severity",
    "ValidationError",
    "ValidationErrorType",
    "ValidationFinding",
    "ValidationReport",
    "assess_readiness",
    "build_handoff_package",
    "error",
    "failing_stages",
    "finding",
    "info",
    "lineage_relations",
    "load_chunks",
    "load_embedding",
    "load_pipeline_assets",
    "load_vectors",
    "present_asset_types",
    "run_load",
    "validate_chunks",
    "validate_embeddings",
    "validate_lineage",
    "validate_vectors",
    "validate_workflow",
    "warning",
]
