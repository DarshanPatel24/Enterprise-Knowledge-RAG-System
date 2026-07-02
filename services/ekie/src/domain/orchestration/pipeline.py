"""Pipeline stage definitions binding the ingestion engines to graph nodes.

Each stage is a pure function of ``(engines, state)`` that invokes exactly one
ingestion engine and returns a normalized :class:`StageOutcome`. Stages carry no
mutable state, so the orchestrator can retry, skip, or replay them safely
(handbook 6.20, ADR-020).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from domain.chunking.engine import ChunkingEngine
from domain.embedding.engine import EmbeddingEngine
from domain.intelligence.engine import DocumentIntelligenceEngine
from domain.orchestration.errors import OrchestrationError, OrchestrationErrorType
from domain.orchestration.state import StageName, WorkflowState
from domain.publishing.engine import VectorPublishingEngine
from domain.transformation.pipeline import TransformationPipeline


@dataclass(frozen=True)
class PipelineEngines:
    """Immutable bundle of the five document-scoped ingestion engines."""

    transformation: TransformationPipeline
    intelligence: DocumentIntelligenceEngine
    chunking: ChunkingEngine
    embedding: EmbeddingEngine
    publishing: VectorPublishingEngine


@dataclass(frozen=True)
class StageOutcome:
    """Normalized result of executing a single stage."""

    asset_id: str
    version: int
    content_hash: str
    created: bool


StageFn = Callable[[PipelineEngines, WorkflowState], StageOutcome]


@dataclass(frozen=True)
class Stage:
    """A named, pure-function ingestion stage."""

    name: StageName
    run: StageFn


def _run_transform(engines: PipelineEngines, state: WorkflowState) -> StageOutcome:
    """Transform the source bytes into a versioned Markdown asset."""
    if state.source_bytes is None:
        raise OrchestrationError(
            OrchestrationErrorType.MISSING_SOURCE,
            "transform stage requires source bytes; provide them to run or resume",
        )
    result = engines.transformation.transform(
        state.document_id,
        state.tenant_id,
        state.source_bytes,
        mime_type=state.mime_type,
    )
    return StageOutcome(
        result.asset_id, result.version, result.content_hash, result.created
    )


def _run_intelligence(engines: PipelineEngines, state: WorkflowState) -> StageOutcome:
    """Enrich the document into a versioned intelligence asset."""
    result = engines.intelligence.enrich(
        state.document_id,
        state.tenant_id,
        provider_override=state.intelligence_provider,
        model_override=state.intelligence_model,
    )
    return StageOutcome(
        result.asset_id, result.version, result.content_hash, result.created
    )


def _run_chunk(engines: PipelineEngines, state: WorkflowState) -> StageOutcome:
    """Chunk the enriched document into a versioned chunk asset."""
    result = engines.chunking.chunk(state.document_id, state.tenant_id)
    return StageOutcome(
        result.asset_id, result.version, result.content_hash, result.created
    )


def _run_embed(engines: PipelineEngines, state: WorkflowState) -> StageOutcome:
    """Embed the chunk asset into a versioned embedding asset."""
    result = engines.embedding.embed(
        state.document_id,
        state.tenant_id,
        provider_override=state.embedding_provider,
        model_override=state.embedding_model,
    )
    return StageOutcome(
        result.asset_id, result.version, result.content_hash, result.created
    )


def _run_publish(engines: PipelineEngines, state: WorkflowState) -> StageOutcome:
    """Publish the embedding asset into the vector store as a vector asset."""
    result = engines.publishing.publish(state.document_id, state.tenant_id)
    return StageOutcome(
        result.asset_id, result.version, result.content_hash, result.created
    )


def default_stages() -> tuple[Stage, ...]:
    """Return the ordered document ingestion pipeline stages.

    The stages follow the deterministic transform -> intelligence -> chunk ->
    embed -> publish order. Repository synchronization is the upstream precursor
    that emits documents into this pipeline and has its own retry recovery.
    """
    return (
        Stage(StageName.TRANSFORM, _run_transform),
        Stage(StageName.INTELLIGENCE, _run_intelligence),
        Stage(StageName.CHUNK, _run_chunk),
        Stage(StageName.EMBED, _run_embed),
        Stage(StageName.PUBLISH, _run_publish),
    )
