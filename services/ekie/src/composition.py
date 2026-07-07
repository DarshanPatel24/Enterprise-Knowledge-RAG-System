"""Composition root: build domain engines from environment-backed settings.

Centralizes engine construction so operational values (providers, models,
limits) come from configuration rather than code. The settings-driven provider
registries select the deterministic local providers by default and swap in real
providers (Ollama, Qdrant) only when configuration selects them, keeping the
offline path dependency-free while enabling production wiring from one place.
"""

from __future__ import annotations

from config.settings import EkieSettings
from domain.chunking.engine import ChunkingEngine
from domain.chunking.policy import ChunkingPolicy
from domain.control_plane import ControlPlaneDatabase
from domain.embedding.engine import EmbeddingEngine
from domain.embedding.policy import EmbeddingPolicy
from domain.embedding.providers import (
    provider_registry_from_settings as build_embedding_provider_registry,
)
from domain.integrations.langchain_resources import (
    LangChainIndex,
    build_embeddings,
    build_qdrant_vector_store,
)
from domain.intelligence.analyzers import analyzers_from_settings
from domain.intelligence.engine import DocumentIntelligenceEngine
from domain.intelligence.policy import IntelligencePolicy
from domain.orchestration import (
    OrchestrationPolicy,
    PipelineEngines,
    WorkflowOrchestrator,
    build_langfuse_client,
)
from domain.orchestration.checkpointer import Checkpointer
from domain.plugins import (
    InProcessSandbox,
    PluginPolicy,
    PluginRegistry,
    PluginValidator,
)
from domain.publishing.engine import VectorPublishingEngine
from domain.publishing.policy import PublishingPolicy
from domain.publishing.providers import (
    provider_registry_from_settings as build_vector_provider_registry,
)
from domain.security import (
    AuditSink,
    EnvSecretProvider,
    InMemoryAuditSink,
    LoggingAuditSink,
    PolicyEngine,
    SecretRegistry,
    SecurityPolicy,
    StagePolicyGuard,
)
from domain.storage import AssetStorage
from domain.transformation.pipeline import TransformationPipeline
from domain.transformation.policy import TransformationPolicy
from domain.validation import PipelineValidator


def build_asset_storage(settings: EkieSettings) -> AssetStorage:
    """Return the appropriate asset storage backend from settings.

    Selects :class:`MinIOAssetStorage` when ``EKIE_STORAGE__ENDPOINT`` is
    non-empty and ``EKIE_ENVIRONMENT`` is not ``local``. The local-first default
    is :class:`LocalFileAssetStorage`, a persistent on-disk store so stage
    payloads survive API/worker restarts (an in-memory store would lose them,
    causing resumed jobs to fail with missing upstream payloads).
    """
    if settings.environment != "local" and settings.storage.endpoint:
        from domain.storage.minio import MinIOAssetStorage

        return MinIOAssetStorage(
            endpoint=settings.storage.endpoint,
            access_key=settings.storage.access_key,
            secret_key=settings.storage.secret_key,
            bucket=settings.storage.bucket,
            secure=settings.storage.secure,
        )
    from domain.storage.local import LocalFileAssetStorage

    return LocalFileAssetStorage(settings.storage.local_path)


def build_intelligence_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> DocumentIntelligenceEngine:
    """Build the document intelligence engine from configuration."""
    return DocumentIntelligenceEngine(
        db,
        storage,
        # Concrete settings expose Literal-typed fields that satisfy the str-typed
        # *SettingsLike Protocols at runtime (mypy flags Protocol invariance only).
        IntelligencePolicy.from_settings(settings.intelligence),  # type: ignore[arg-type]
        analyzers=analyzers_from_settings(settings.intelligence),
    )


def build_transformation_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> TransformationPipeline:
    """Build the document transformation pipeline from configuration."""
    return TransformationPipeline(
        db, storage, TransformationPolicy.from_settings(settings.transformation)
    )


def build_chunking_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> ChunkingEngine:
    """Build the intelligent chunking engine from configuration."""
    return ChunkingEngine(db, storage, ChunkingPolicy.from_settings(settings.chunking))


def build_embedding_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> EmbeddingEngine:
    """Build the embedding engine with the configured provider registry."""
    from domain.control_plane.progress import ControlPlaneProgressReporter

    return EmbeddingEngine(
        db,
        storage,
        EmbeddingPolicy.from_settings(settings.embedding),  # type: ignore[arg-type]
        provider_registry=build_embedding_provider_registry(
            settings.embedding  # type: ignore[arg-type]
        ),
        progress_reporter=ControlPlaneProgressReporter(db),
    )


def build_publishing_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> VectorPublishingEngine:
    """Build the vector publishing engine with the configured provider registry."""
    from domain.control_plane.progress import ControlPlaneProgressReporter

    return VectorPublishingEngine(
        db,
        storage,
        PublishingPolicy.from_settings(settings.publishing),  # type: ignore[arg-type]
        provider_registry=build_vector_provider_registry(
            settings.publishing,  # type: ignore[arg-type]
            settings.qdrant,
        ),
        progress_reporter=ControlPlaneProgressReporter(db),
    )


def build_pipeline_engines(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> PipelineEngines:
    """Build the five document-scoped ingestion engines as one bundle."""
    return PipelineEngines(
        transformation=build_transformation_engine(settings, db, storage),
        intelligence=build_intelligence_engine(settings, db, storage),
        chunking=build_chunking_engine(settings, db, storage),
        embedding=build_embedding_engine(settings, db, storage),
        publishing=build_publishing_engine(settings, db, storage),
    )


def build_workflow_orchestrator(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    *,
    checkpointer: Checkpointer | None = None,
) -> WorkflowOrchestrator:
    """Build the ingestion workflow orchestrator from configuration."""
    langfuse_client = (
        build_langfuse_client(settings.observability)
        if settings.orchestration.enable_tracing
        else None
    )
    return WorkflowOrchestrator(
        db,
        build_pipeline_engines(settings, db, storage),
        OrchestrationPolicy.from_settings(settings.orchestration),
        checkpointer=checkpointer,
        tracer_callbacks=langfuse_client,
    )


def build_security_policy(settings: EkieSettings) -> SecurityPolicy:
    """Build the security and governance policy from configuration."""
    return SecurityPolicy.from_settings(settings.security, settings.governance)


def build_secret_provider(
    settings: EkieSettings,
    *,
    registry: SecretRegistry | None = None,
) -> EnvSecretProvider:
    """Build the ephemeral secret provider from environment-backed settings.

    Only non-empty configured secrets are exposed. Resolving a secret registers
    its value for log redaction, keeping secrets out of logs (handbook 17.8).
    """
    secrets = {
        name: value
        for name, value in (
            ("storage_secret_key", settings.storage.secret_key),
            ("control_plane_password", settings.control_plane.password),
            ("langfuse_public_key", settings.observability.langfuse_public_key),
            ("langfuse_secret_key", settings.observability.langfuse_secret_key),
        )
        if value
    }
    provider = EnvSecretProvider(secrets, registry=registry)
    for value in secrets.values():
        provider.registry.register(value)
    return provider


def _build_audit_sink(settings: EkieSettings) -> AuditSink:
    """Select the configured audit sink (logging by default)."""
    if settings.governance.audit_sink == "memory":
        return InMemoryAuditSink()
    return LoggingAuditSink()


def build_stage_guard(
    settings: EkieSettings,
    *,
    audit_sink: AuditSink | None = None,
) -> StagePolicyGuard:
    """Build the per-stage governance guard from configuration."""
    policy = build_security_policy(settings)
    return StagePolicyGuard(
        policy,
        PolicyEngine(policy),
        audit_sink or _build_audit_sink(settings),
    )


def build_plugin_registry(settings: EkieSettings) -> PluginRegistry:
    """Build the controlled plugin registry with sandbox validation."""
    sandbox = InProcessSandbox()
    validator = PluginValidator(PluginPolicy.from_settings(settings.plugins), sandbox)
    return PluginRegistry(validator, sandbox)


def build_pipeline_validator(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> PipelineValidator:
    """Build the end-to-end pipeline validator over the Control Plane and storage."""
    return PipelineValidator(db, storage)


def build_langchain_index(
    settings: EkieSettings, *, create_collection: bool = False
) -> LangChainIndex:
    """Build a LangChain embedding model + Qdrant vector store from settings.

    A single config-driven template that mirrors a standard RAG index: it uses
    the configured embedding provider (huggingface/ollama) and the canonical
    Qdrant connection. This is a convenience/index seam; the verified publishing
    engine keeps its own Qdrant client and verification path.
    """
    embeddings = build_embeddings(
        settings.embedding.provider,
        settings.embedding.default_model,
        base_url=settings.embedding.ollama_base_url,
    )
    vector_store = build_qdrant_vector_store(
        embeddings,
        collection=settings.publishing.default_collection,
        host=settings.qdrant.host,
        port=settings.qdrant.port,
        url=settings.qdrant.url or None,
        api_key=settings.qdrant.api_key or None,
        distance=settings.embedding.distance_metric,
        vector_size=settings.embedding.dimension,
        create_collection=create_collection,
    )
    return LangChainIndex(embeddings=embeddings, vector_store=vector_store)


__all__ = [
    "build_chunking_engine",
    "build_embedding_engine",
    "build_intelligence_engine",
    "build_langchain_index",
    "build_pipeline_engines",
    "build_pipeline_validator",
    "build_plugin_registry",
    "build_publishing_engine",
    "build_secret_provider",
    "build_security_policy",
    "build_stage_guard",
    "build_transformation_engine",
    "build_workflow_orchestrator",
]
