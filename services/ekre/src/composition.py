"""Composition root: build EKRE foundations from settings.

Wires the settings module into engine-owned domain objects (config over code).
Domain packages stay independent of the settings module; this root is the single
place that reads settings and injects dependencies.
"""

from __future__ import annotations

import uuid
from typing import Any

from config.settings import EkreSettings, EmbeddingSettings
from domain.assembly import AssemblyPolicy, ContextAssemblyEngine
from domain.connectors import (
    InMemoryRepositoryConnector,
    QdrantRetrievalConnector,
    RepositoryConnector,
)
from domain.execution import (
    ExecutionPolicy,
    ExecutionScheduler,
    RetrievalOrchestrator,
    WorkerRegistry,
    runner_from_policy,
)
from domain.fusion import CandidateCollector, CandidateFusion, FusionPolicy
from domain.governance import (
    AuditAction,
    AuditResult,
    AuditSink,
    InMemoryAuditSink,
    LoggingAuditSink,
    Masker,
    MaskingConfig,
    RetrievalPipeline,
    build_audit_record,
)
from domain.inheritance import (
    EmbeddingProfile,
    InheritanceResolver,
    QdrantSchemaReader,
)
from domain.integrations import (
    RetrievalResources,
    build_embeddings,
    build_qdrant_vector_store,
    build_retriever,
)
from domain.observability import build_langfuse_callbacks, configure_logging
from domain.query import (
    IntentClassificationEngine,
    QueryEnrichmentEngine,
    QueryIntelligenceEngine,
    QueryLlmInterpreter,
    QueryPlanner,
    QueryPolicy,
    QueryUnderstandingEngine,
    default_vocabulary,
)
from domain.ranking import (
    CrossEncoderReranker,
    IdentityReranker,
    RankingEngine,
    RankingPolicy,
    Reranker,
)
from domain.readiness import ReadinessReport, assess_deployment_readiness
from domain.resilience import CircuitBreaker, TenantConcurrencyLimiter
from domain.retrieval import (
    EmbeddingAdapter,
    LangChainEmbeddingAdapter,
    LocalHashEmbeddingAdapter,
    build_worker_registry,
)
from domain.security import SecurityContextValidator


def configure_observability(settings: EkreSettings) -> None:
    """Install structured JSON logging from the observability settings."""
    configure_logging(
        service_name=settings.observability.service_name,
        log_level=settings.observability.log_level,
    )


def build_security_validator(settings: EkreSettings) -> SecurityContextValidator:
    """Build the security context ingress validator from settings."""
    return SecurityContextValidator.from_settings(settings.security)  # type: ignore[arg-type]


def build_inheritance_resolver(settings: EkreSettings) -> InheritanceResolver:
    """Build the inheritance resolver backed by a Qdrant schema reader.

    The Qdrant client is constructed lazily by the reader so the resolver can be
    built without a live connection; the connection is only opened on ``resolve``.
    """
    qdrant = settings.qdrant

    def _client_factory() -> Any:  # noqa: ANN401 - QdrantClient type is lazy
        from domain.integrations import build_qdrant_client

        return build_qdrant_client(
            host=qdrant.host,
            port=qdrant.port,
            url=qdrant.url or None,
            api_key=qdrant.api_key.get_secret_value() or None,
            timeout_seconds=qdrant.request_timeout_seconds,
        )

    reader = QdrantSchemaReader(_client_factory)
    # Concrete settings' Literal fields satisfy the str-typed Protocol at runtime
    # (Protocol invariance quirk).
    return InheritanceResolver.from_settings(reader, settings.inheritance)  # type: ignore[arg-type]


def resolve_embedding_profile(
    settings: EkreSettings, *, collection: str | None = None
) -> EmbeddingProfile:
    """Resolve the inherited embedding profile for the target collection."""
    resolver = build_inheritance_resolver(settings)
    target = collection or settings.retrieval.default_collection
    return resolver.resolve(target)


def build_retrieval_resources(
    settings: EkreSettings,
    profile: EmbeddingProfile,
    *,
    top_k: int | None = None,
) -> RetrievalResources:
    """Build embeddings, Qdrant vector store, and retriever for a resolved profile.

    The embedding model and distance metric come from the inherited ``profile``
    (never hardcoded); the provider and connection come from settings.
    """
    embedding_settings = settings.embedding
    _ensure_model_allowed(embedding_settings, profile.embedding_model)
    embeddings = build_embeddings(
        embedding_settings.provider,
        profile.embedding_model,
        base_url=embedding_settings.base_url,
    )
    vector_store = build_qdrant_vector_store(
        embeddings,
        collection=profile.collection,
        host=settings.qdrant.host,
        port=settings.qdrant.port,
        url=settings.qdrant.url or None,
        api_key=settings.qdrant.api_key.get_secret_value() or None,
        distance=profile.distance_metric.value,
        vector_size=profile.dimension,
        create_collection=False,
        timeout_seconds=settings.qdrant.request_timeout_seconds,
    )
    retriever = build_retriever(
        vector_store,
        search_type=settings.retrieval.search_type,
        k=top_k or settings.retrieval.default_top_k,
    )
    return RetrievalResources(
        embeddings=embeddings,
        vector_store=vector_store,
        retriever=retriever,
    )


def build_tracing_callbacks(settings: EkreSettings) -> list[object]:
    """Return Langfuse callbacks from settings, or an empty list when disabled."""
    return list(build_langfuse_callbacks(settings.observability))


def build_query_intelligence_engine(settings: EkreSettings) -> QueryIntelligenceEngine:
    """Build the deterministic query intelligence pipeline from settings.

    The optional LLM interpreter is attached only when enabled; it always
    degrades to the deterministic understanding engine, so planning stays
    reproducible.
    """
    policy = QueryPolicy.from_settings(settings.query)  # type: ignore[arg-type]
    vocabulary = default_vocabulary()
    understanding = QueryUnderstandingEngine(policy, vocabulary=vocabulary)
    intent = IntentClassificationEngine(policy)
    enrichment = QueryEnrichmentEngine(vocabulary=vocabulary)
    planner = QueryPlanner(
        vector_timeout_ms=settings.retrieval.budget_vector_ms,
        total_timeout_ms=settings.retrieval.budget_total_ms,
    )
    interpreter = (
        QueryLlmInterpreter(policy) if settings.query.enable_llm_interpreter else None
    )
    return QueryIntelligenceEngine(
        understanding,
        intent,
        enrichment,
        planner,
        llm_interpreter=interpreter,
    )


def build_repository_connector(settings: EkreSettings) -> RepositoryConnector:
    """Build the repository connector selected by settings (in-memory default)."""
    if settings.workers.connector == "qdrant":
        qdrant = settings.qdrant
        return QdrantRetrievalConnector(
            host=qdrant.host,
            port=qdrant.port,
            url=qdrant.url,
            api_key=qdrant.api_key.get_secret_value(),
            timeout_seconds=qdrant.request_timeout_seconds,
            metadata_key=qdrant.payload_metadata_key,
        )
    return InMemoryRepositoryConnector()


def build_query_embedding_adapter(settings: EkreSettings) -> EmbeddingAdapter:
    """Build the query embedding adapter (deterministic local hash by default).

    The ``langchain`` embedder inherits the embedding model and dimension EKIE
    published (never hardcoded); the offline default uses a deterministic hash.
    Device/precision (for example ``torch_dtype=float16``) are threaded into the
    HuggingFace model so the query model runs on the GPU, exactly as EKIE.
    """
    if settings.workers.query_embedder == "langchain":
        embedding = settings.embedding
        profile = resolve_embedding_profile(settings)
        _ensure_model_allowed(embedding, profile.embedding_model)
        return LangChainEmbeddingAdapter(
            embedding.provider,
            profile.embedding_model,
            dimension=profile.dimension,
            base_url=embedding.base_url,
            model_kwargs=_huggingface_model_kwargs(embedding.device, embedding.torch_dtype),
        )
    return LocalHashEmbeddingAdapter(settings.workers.local_embedding_dimension)


def _ensure_model_allowed(embedding_settings: EmbeddingSettings, model: str) -> None:
    """Reject an inherited embedding model that is not on the configured allowlist.

    The embedding model name is inherited from the Qdrant vector payload; an
    allowlist prevents a poisoned or unexpected payload from causing EKRE to load
    an untrusted model. An empty allowlist permits any inherited model.
    """
    allowed = embedding_settings.allowed_model_set()
    if allowed and model not in allowed:
        raise ValueError(
            f"embedding model {model!r} is not in the configured allowlist"
        )


def _huggingface_model_kwargs(device: str, torch_dtype: str) -> dict[str, Any]:
    """Build HuggingFace sentence-transformers kwargs for device/precision.

    Leaving either value at ``auto`` preserves the library defaults (GPU
    auto-detect, fp32); ``torch_dtype=float16`` halves VRAM so large models fit a
    limited-VRAM GPU. Mirrors the EKIE embedding provider.
    """
    st_kwargs: dict[str, Any] = {}
    if device and device != "auto":
        st_kwargs["device"] = device
    if torch_dtype and torch_dtype != "auto":
        st_kwargs["model_kwargs"] = {"torch_dtype": torch_dtype}
    return {"model_kwargs": st_kwargs} if st_kwargs else {}


def build_retrieval_worker_registry(
    settings: EkreSettings,
    *,
    connector: RepositoryConnector | None = None,
    adapter: EmbeddingAdapter | None = None,
) -> WorkerRegistry:
    """Assemble the vector/keyword/metadata workers for the configured connector."""
    resolved_connector = connector or build_repository_connector(settings)
    resolved_adapter = adapter or build_query_embedding_adapter(settings)
    return build_worker_registry(
        resolved_connector,
        resolved_adapter,
        collection=settings.retrieval.default_collection,
        require_security_context=settings.security.require_security_context,
        require_tenant_scope=settings.security.require_tenant_scope,
    )


def build_retrieval_orchestrator(
    settings: EkreSettings,
    *,
    registry: WorkerRegistry | None = None,
    adapter: EmbeddingAdapter | None = None,
) -> RetrievalOrchestrator:
    """Build the retrieval execution orchestrator from settings.

    When no registry is supplied, the real vector/keyword/metadata workers are
    assembled for the configured connector (in-memory + deterministic embedder by
    default), so the orchestrator retrieves and filters candidates end to end.
    A pre-built ``adapter`` may be injected so the query embedding model is loaded
    once and shared across requests.
    """
    policy = ExecutionPolicy.from_settings(settings.execution)  # type: ignore[arg-type]
    scheduler = ExecutionScheduler(policy)
    runner = runner_from_policy(policy.runner, max_workers=policy.max_parallel_workers)
    return RetrievalOrchestrator(
        registry or build_retrieval_worker_registry(settings, adapter=adapter),
        scheduler,
        runner,
        policy=policy,
    )


def build_candidate_collector() -> CandidateCollector:
    """Build the unified candidate collector."""
    return CandidateCollector()


_FUSION_POLICIES = {
    "chunk": FusionPolicy.CHUNK_IDENTITY,
    "document": FusionPolicy.DOCUMENT_IDENTITY,
    "strict": FusionPolicy.STRICT_IDENTITY,
}


def build_candidate_fusion(settings: EkreSettings) -> CandidateFusion:
    """Build the candidate fusion engine from settings."""
    policy = _FUSION_POLICIES[settings.fusion.identity_policy]
    return CandidateFusion(policy, rrf_k=settings.fusion.rrf_k)


def build_reranker(settings: EkreSettings) -> Reranker:
    """Build the reranker: the cross-encoder reranker or the identity default.

    The cross-encoder is used only when enabled and a model is configured;
    otherwise the deterministic identity reranker preserves the evidence order.
    """
    ranking = settings.ranking
    if ranking.enable_reranker and ranking.reranker_model:
        return CrossEncoderReranker(ranking)
    return IdentityReranker()


def build_ranking_engine(
    settings: EkreSettings, *, reranker: Reranker | None = None
) -> RankingEngine:
    """Build the deterministic, auditable ranking engine from settings.

    A pre-built ``reranker`` may be injected so the cross-encoder model loads once
    (at startup) and is reused across requests instead of on first rerank.
    """
    policy = RankingPolicy.from_settings(settings.ranking)
    return RankingEngine(policy, reranker=reranker or build_reranker(settings))


def build_context_assembly_engine(settings: EkreSettings) -> ContextAssemblyEngine:
    """Build the context assembly engine that packages the EKCP handoff."""
    policy = AssemblyPolicy.from_settings(settings.assembly)  # type: ignore[arg-type]
    return ContextAssemblyEngine(policy)


def build_audit_sink(settings: EkreSettings) -> AuditSink:
    """Build the audit sink selected by settings (structured logging default)."""
    if settings.governance.audit_sink == "memory":
        return InMemoryAuditSink()
    return LoggingAuditSink()


def record_access_denied(
    settings: EkreSettings, *, actor: str, tenant_id: str, reason: str
) -> None:
    """Write an ACCESS_DENIED audit record for a rejected retrieval request.

    Authorization failures (missing/invalid context, tenant mismatch, unknown
    clearance) are security-relevant events and must be auditable, not only
    logged. Honors the ``enable_audit`` governance toggle.
    """
    if not settings.governance.enable_audit:
        return
    from domain.observability import get_correlation_id

    build_audit_sink(settings).record(
        build_audit_record(
            action=AuditAction.ACCESS_DENIED,
            result=AuditResult.DENIED,
            actor=actor or "unknown",
            tenant_id=tenant_id,
            execution_id=f"denied-{uuid.uuid4().hex[:12]}",
            correlation_id=get_correlation_id(),
            policy_version=settings.governance.policy_version,
            detail={"reason": reason},
        )
    )


def build_masker(settings: EkreSettings) -> Masker:
    """Build the PII masker from governance settings."""
    governance = settings.governance
    return Masker(
        MaskingConfig(
            enabled=governance.enable_masking,
            email=governance.mask_email,
            phone=governance.mask_phone,
            ssn=governance.mask_ssn,
            credit_card=governance.mask_credit_card,
        )
    )


def build_retrieval_pipeline(
    settings: EkreSettings,
    *,
    audit_sink: AuditSink | None = None,
    adapter: EmbeddingAdapter | None = None,
    reranker: Reranker | None = None,
) -> RetrievalPipeline:
    """Assemble the full traced, audited, masked retrieval pipeline.

    A pre-built ``adapter`` and ``reranker`` may be injected so the embedding and
    cross-encoder models load once (at startup) and are reused across requests
    instead of per call.
    """
    return RetrievalPipeline(
        build_query_intelligence_engine(settings),
        build_retrieval_orchestrator(settings, adapter=adapter),
        build_candidate_collector(),
        build_candidate_fusion(settings),
        build_ranking_engine(settings, reranker=reranker),
        build_context_assembly_engine(settings),
        build_masker(settings),
        audit_sink or build_audit_sink(settings),
        budget_ms=settings.governance.total_latency_budget_ms,
        enable_audit=settings.governance.enable_audit,
        policy_version=settings.governance.policy_version,
    )


def build_circuit_breaker(settings: EkreSettings) -> CircuitBreaker:
    """Build a circuit breaker from the deployment settings."""
    return CircuitBreaker(
        failure_threshold=settings.deployment.circuit_breaker_threshold,
        reset_timeout_seconds=settings.deployment.circuit_breaker_reset_seconds,
    )


def build_tenant_limiter(settings: EkreSettings) -> TenantConcurrencyLimiter:
    """Build the multi-tenant concurrency limiter from the deployment settings."""
    return TenantConcurrencyLimiter(settings.deployment.tenant_max_concurrent)


def build_deployment_readiness(settings: EkreSettings) -> ReadinessReport:
    """Assess deployment readiness from the deployment settings."""
    return assess_deployment_readiness(settings.deployment)


__all__ = [
    "build_audit_sink",
    "build_candidate_collector",
    "build_candidate_fusion",
    "build_circuit_breaker",
    "build_context_assembly_engine",
    "build_deployment_readiness",
    "build_inheritance_resolver",
    "build_masker",
    "build_query_embedding_adapter",
    "build_query_intelligence_engine",
    "build_ranking_engine",
    "build_reranker",
    "build_repository_connector",
    "build_retrieval_orchestrator",
    "build_retrieval_pipeline",
    "build_retrieval_resources",
    "build_retrieval_worker_registry",
    "build_security_validator",
    "build_tenant_limiter",
    "build_tracing_callbacks",
    "configure_observability",
    "record_access_denied",
    "resolve_embedding_profile",
]
