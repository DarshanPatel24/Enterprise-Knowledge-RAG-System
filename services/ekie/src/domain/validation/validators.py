"""Deterministic pipeline validators (handbook Chapter 20, EKIE-S9-1/S9-2).

Each validator inspects one facet of a completed ingestion and returns a
:class:`ValidationReport`. Validators never raise on data-quality problems; they
record findings so a pipeline-level report can aggregate them. This guarantees
end-to-end verification of data integrity, lineage completeness, and per-stage
correctness with no silent data loss.
"""

from __future__ import annotations

from domain.chunking.models import ChunkDocument
from domain.control_plane import AssetType, ControlPlaneDatabase
from domain.embedding.models import EmbeddingDocument
from domain.embedding.validation import EmbeddingValidator
from domain.orchestration.engine import WorkflowResult
from domain.orchestration.state import StageName, WorkflowStatus
from domain.publishing.models import PublishedVectorSet
from domain.validation.assets import lineage_relations, present_asset_types
from domain.validation.report import ValidationReport, error, info, warning

_EXPECTED_STAGES: tuple[StageName, ...] = (
    StageName.TRANSFORM,
    StageName.INTELLIGENCE,
    StageName.CHUNK,
    StageName.EMBED,
    StageName.PUBLISH,
)

_EXPECTED_ASSET_TYPES: frozenset[AssetType] = frozenset(
    {
        AssetType.MARKDOWN,
        AssetType.INTELLIGENCE,
        AssetType.CHUNKS,
        AssetType.EMBEDDING,
        AssetType.VECTOR,
    }
)

_EXPECTED_LINEAGE: frozenset[str] = frozenset(
    {
        "derived_from_markdown",
        "chunked_from_intelligence",
        "embedded_from_chunks",
        "published_from_embedding",
    }
)


def validate_workflow(result: WorkflowResult) -> ValidationReport:
    """Validate that a workflow completed all stages without dead-lettering."""
    findings = []
    if result.status is not WorkflowStatus.COMPLETED:
        findings.append(
            error(
                "workflow.status",
                f"workflow status is {result.status.value!r}, expected 'completed'",
            )
        )
    if result.failure is not None:
        findings.append(
            error(
                "workflow.failure",
                f"stage {result.failure.stage.value!r} failed: "
                f"{result.failure.error_type} ({result.failure.message})",
            )
        )
    missing = [s for s in _EXPECTED_STAGES if s not in result.completed_stages]
    if missing:
        findings.append(
            error(
                "workflow.stages",
                "missing completed stages: "
                + ", ".join(s.value for s in missing),
            )
        )
    else:
        findings.append(
            info("workflow.stages", "all five ingestion stages completed")
        )
    return ValidationReport(name="workflow", findings=tuple(findings))


def validate_lineage(
    db: ControlPlaneDatabase, *, document_id: str
) -> ValidationReport:
    """Validate that every asset type and lineage relation is present."""
    findings = []
    present = present_asset_types(db, document_id)
    missing_assets = _EXPECTED_ASSET_TYPES - present
    if missing_assets:
        findings.append(
            error(
                "lineage.assets",
                "missing asset types: "
                + ", ".join(sorted(a.value for a in missing_assets)),
            )
        )
    relations = lineage_relations(db, document_id)
    missing_relations = _EXPECTED_LINEAGE - relations
    if missing_relations:
        findings.append(
            error(
                "lineage.relations",
                "missing lineage relations: "
                + ", ".join(sorted(missing_relations)),
            )
        )
    if not missing_assets and not missing_relations:
        findings.append(
            info("lineage", "asset chain and lineage relations are complete")
        )
    return ValidationReport(name="lineage", findings=tuple(findings))


def validate_chunks(chunks: ChunkDocument) -> ValidationReport:
    """Validate chunk counts, token totals, identity, and content integrity."""
    findings = []
    if chunks.chunk_count != len(chunks.chunks):
        findings.append(
            error(
                "chunks.count",
                f"declared chunk_count {chunks.chunk_count} does not match "
                f"{len(chunks.chunks)} chunk records",
            )
        )
    token_sum = sum(c.metadata.token_count for c in chunks.chunks)
    if token_sum != chunks.total_tokens:
        findings.append(
            error(
                "chunks.tokens",
                f"declared total_tokens {chunks.total_tokens} does not match "
                f"summed token_count {token_sum}",
            )
        )
    ids = [c.metadata.chunk_id for c in chunks.chunks]
    if len(ids) != len(set(ids)):
        findings.append(error("chunks.identity", "duplicate chunk ids detected"))
    for chunk in chunks.chunks:
        if not chunk.content.strip():
            findings.append(
                error(
                    "chunks.content",
                    f"chunk {chunk.metadata.chunk_id!r} has empty content",
                )
            )
        if chunk.metadata.token_count <= 0:
            findings.append(
                error(
                    "chunks.tokens",
                    f"chunk {chunk.metadata.chunk_id!r} has non-positive tokens",
                )
            )
    if not findings:
        findings.append(
            info("chunks", f"{len(chunks.chunks)} chunks are internally consistent")
        )
    return ValidationReport(name="chunks", findings=tuple(findings))


def validate_embeddings(
    chunks: ChunkDocument, embedding: EmbeddingDocument
) -> ValidationReport:
    """Validate embedding coverage, dimensions, and vector quality."""
    findings = []
    if embedding.embedding_count != len(embedding.records):
        findings.append(
            error(
                "embeddings.count",
                f"declared embedding_count {embedding.embedding_count} does not "
                f"match {len(embedding.records)} records",
            )
        )
    chunk_ids = {c.metadata.chunk_id for c in chunks.chunks}
    embedded_ids = {r.chunk_id for r in embedding.records}
    uncovered = chunk_ids - embedded_ids
    if uncovered:
        findings.append(
            error(
                "embeddings.coverage",
                f"{len(uncovered)} chunk(s) have no embedding (data loss)",
            )
        )
    validator = EmbeddingValidator(embedding.dimension)
    for record in embedding.records:
        report = validator.validate(record.values)
        if not report.valid:
            findings.append(
                error(
                    "embeddings.vector",
                    f"embedding {record.embedding_id!r} invalid: "
                    + "; ".join(report.messages),
                )
            )
    if not findings:
        findings.append(
            info(
                "embeddings",
                f"{len(embedding.records)} vectors of dimension "
                f"{embedding.dimension} validated",
            )
        )
    return ValidationReport(name="embeddings", findings=tuple(findings))


def validate_vectors(
    embedding: EmbeddingDocument, vectors: PublishedVectorSet
) -> ValidationReport:
    """Validate published-vector coverage and dimension against embeddings."""
    findings = []
    if vectors.vector_count != len(vectors.records):
        findings.append(
            error(
                "vectors.count",
                f"declared vector_count {vectors.vector_count} does not match "
                f"{len(vectors.records)} records",
            )
        )
    if vectors.dimension != embedding.dimension:
        findings.append(
            error(
                "vectors.dimension",
                f"published dimension {vectors.dimension} does not match "
                f"embedding dimension {embedding.dimension}",
            )
        )
    embedded_ids = {r.chunk_id for r in embedding.records}
    published_ids = {r.chunk_id for r in vectors.records}
    uncovered = embedded_ids - published_ids
    if uncovered:
        findings.append(
            error(
                "vectors.coverage",
                f"{len(uncovered)} embedded chunk(s) not published (data loss)",
            )
        )
    unpublished = [
        r.vector_id
        for r in vectors.records
        if r.state.value not in {"published", "verified"}
    ]
    if unpublished:
        findings.append(
            warning(
                "vectors.state",
                f"{len(unpublished)} vector(s) are not in a published state",
            )
        )
    if not findings:
        findings.append(
            info("vectors", f"{len(vectors.records)} vectors published and covered")
        )
    return ValidationReport(name="vectors", findings=tuple(findings))
