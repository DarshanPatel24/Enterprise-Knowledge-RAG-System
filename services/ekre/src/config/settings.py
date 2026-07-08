"""Environment-backed configuration for the EKRE service.

All operational values are configuration-driven (configuration over code). No
credentials, endpoints, models, or limits are hardcoded; values load from the
process environment or a local ``.env`` file with the ``EKRE_`` prefix.

Sameness rule: EKRE queries the same Qdrant collection with the same embedding
model and distance metric that EKIE used to publish the stored vectors. The
embedding model, dimension, and distance metric are inherited from the
collection at runtime (see ``domain.inheritance``); the values declared here are
documented fallbacks only.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the .env file co-located with services/ekre/ regardless of
# the process working directory, preventing silent settings fall-through when
# uvicorn or scripts start from the repository root.
# Path hierarchy from this file (services/ekre/src/config/settings.py):
#   parents[0] = config/
#   parents[1] = src/
#   parents[2] = services/ekre/   <-- .env lives here
_ENV_FILE = str(Path(__file__).resolve().parents[2] / ".env")


class QdrantSettings(BaseSettings):
    """Qdrant vector database connection settings (shared with EKIE)."""

    model_config = SettingsConfigDict(env_prefix="EKRE_QDRANT__", extra="ignore")

    host: str = "localhost"
    port: int = 6333
    url: str = ""
    api_key: SecretStr = SecretStr("")
    request_timeout_seconds: float = 30.0
    # Payload key under which EKIE nests governance metadata (tenant_id,
    # classification_clearance, document_id, ...). Filters and payload reads use
    # this prefix; set to "" if a repository stores those fields at the top level.
    payload_metadata_key: str = "metadata"


class ObservabilitySettings(BaseSettings):
    """Observability settings for logging, tracing, and Langfuse."""

    model_config = SettingsConfigDict(env_prefix="EKRE_OBSERVABILITY__", extra="ignore")

    log_level: str = "INFO"
    service_name: str = "ekre"
    langfuse_enabled: bool = False
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    otel_exporter_endpoint: str | None = None


class RetrievalSettings(BaseSettings):
    """Retrieval behavior, profile, and stage latency budget settings.

    Latency budgets encode the handbook non-functional targets so the stage
    timeline can flag any stage that exceeds its budget.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_RETRIEVAL__", extra="ignore")

    default_collection: str = "enterprise_documents"
    search_type: Literal["similarity", "mmr"] = "similarity"
    default_top_k: int = Field(default=5, gt=0)
    # Optional allowlist of collections a client may target (comma-separated).
    # Prevents collection enumeration/access beyond the intended set. Empty means
    # any collection is permitted; the default collection is always allowed.
    allowed_collections: str = ""
    budget_query_understanding_ms: float = 20.0
    budget_vector_ms: float = 150.0
    budget_ranking_ms: float = 100.0
    budget_assembly_ms: float = 50.0
    budget_total_ms: float = 500.0

    def allowed_collection_set(self) -> frozenset[str]:
        """Return the permitted collections (always including the default)."""
        names = {name.strip() for name in self.allowed_collections.split(",") if name.strip()}
        names.add(self.default_collection)
        return frozenset(names)

    def latency_budgets(self) -> dict[str, float]:
        """Return the per-stage latency budgets keyed by stage name."""
        return {
            "query_understanding": self.budget_query_understanding_ms,
            "vector": self.budget_vector_ms,
            "ranking": self.budget_ranking_ms,
            "assembly": self.budget_assembly_ms,
            "total": self.budget_total_ms,
        }


class EmbeddingSettings(BaseSettings):
    """Query embedding runtime settings.

    ``provider`` selects how the query text is embedded (which library loads the
    model); it must be able to load the same model EKIE used. The model name,
    dimension, and distance metric are inherited from the collection, so the
    fallback model here is used only when inheritance cannot resolve the model.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_EMBEDDING__", extra="ignore")

    provider: Literal["ollama", "huggingface"] = "huggingface"
    fallback_model: str = ""
    base_url: str = "http://localhost:11434"
    request_timeout_seconds: float = 60.0
    normalize_vectors: bool = True
    device: str = "auto"
    torch_dtype: str = "auto"
    # Optional allowlist of embedding model identifiers (comma-separated). The
    # embedding model is inherited from the Qdrant vector payload, so an
    # allowlist prevents a poisoned payload from loading an unexpected model.
    # Empty means allow any inherited model (default).
    allowed_models: str = ""

    def allowed_model_set(self) -> frozenset[str]:
        """Return the configured allowlist of embedding model identifiers."""
        return frozenset(name.strip() for name in self.allowed_models.split(",") if name.strip())


class InheritanceSettings(BaseSettings):
    """Settings governing inheritance of embedding and distance metric from EKIE.

    Inheritance reads the live Qdrant collection schema (distance metric and
    dimension) and vector payload metadata (embedding model). Fallbacks apply
    only when ``allow_config_fallback`` is true and a value cannot be resolved.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_INHERITANCE__", extra="ignore")

    allow_config_fallback: bool = True
    fallback_embedding_model: str = ""
    fallback_dimension: int = Field(default=0, ge=0)
    fallback_distance_metric: Literal["cosine", "dot_product", "euclidean"] = "cosine"


class SecuritySettings(BaseSettings):
    """Security context ingress settings enforced before ranking.

    When ``require_security_context`` is true every retrieval request must carry
    a valid security context; unauthorized candidates never enter the pool.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_SECURITY__", extra="ignore")

    require_security_context: bool = True
    # Enforce tenant isolation: retrieval is filtered to the requesting tenant at
    # the repository boundary and re-checked in-process (defense in depth).
    require_tenant_scope: bool = True
    default_clearance: Literal["public", "internal", "confidential", "restricted"] = "public"
    # Verifiable trust boundary. When true, the security context must be supplied
    # as a signed JWT (header X-Security-Context) minted by the trusted caller
    # (EKCP) rather than self-asserted in the request body. Default off so the
    # boundary can be enabled once the caller starts signing.
    require_signed_context: bool = False
    context_signing_secret: SecretStr = SecretStr("")
    context_signing_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    context_issuer: str = ""
    context_audience: str = ""
    context_leeway_seconds: int = Field(default=30, ge=0)

    def context_signing_secret_value(self) -> str:
        """Return the raw signing secret for the context verifier."""
        return self.context_signing_secret.get_secret_value()


class QueryIntelligenceSettings(BaseSettings):
    """Query intelligence (understanding, intent, enrichment, planning) settings.

    The pipeline is deterministic by default. The optional LLM interpreter is
    feature-flagged off and always degrades to the deterministic path, so
    retrieval planning stays reproducible.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_QUERY__", extra="ignore")

    max_query_length: int = Field(default=2048, gt=0)
    default_language: str = "en"
    # Candidate counts selected per retrieval profile (operational tunables).
    candidate_count_precision: int = Field(default=5, gt=0)
    candidate_count_recall: int = Field(default=50, gt=0)
    candidate_count_balanced: int = Field(default=20, gt=0)
    candidate_count_compliance: int = Field(default=30, gt=0)
    candidate_count_performance: int = Field(default=10, gt=0)
    # Optional LangChain LLM query interpreter (deterministic fallback when off).
    enable_llm_interpreter: bool = False
    llm_provider: Literal["ollama", "huggingface"] = "huggingface"
    llm_model: str = ""
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.0
    llm_request_timeout_seconds: float = 60.0

    def candidate_counts(self) -> dict[str, int]:
        """Return the candidate count per retrieval profile keyed by profile name."""
        return {
            "precision": self.candidate_count_precision,
            "recall": self.candidate_count_recall,
            "balanced": self.candidate_count_balanced,
            "compliance": self.candidate_count_compliance,
            "performance": self.candidate_count_performance,
        }


class ExecutionSettings(BaseSettings):
    """Retrieval execution core settings (orchestration, scheduling, workers).

    Execution is deterministic and parallel by default. Failures are isolated:
    with ``fail_open`` true an all-worker failure returns an empty result rather
    than raising, so one broken engine never terminates a query.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_EXECUTION__", extra="ignore")

    runner: Literal["concurrent", "langgraph"] = "concurrent"
    max_parallel_workers: int = Field(default=4, gt=0)
    default_task_timeout_ms: float = Field(default=150.0, gt=0.0)
    max_attempts_per_task: int = Field(default=1, gt=0)
    admission_enabled: bool = True
    fail_open: bool = True
    enable_tracing: bool = False


class WorkerSettings(BaseSettings):
    """Retrieval worker + repository connector settings.

    Local-first defaults: an in-memory connector and a deterministic hash query
    embedder keep retrieval fully offline. Switch to ``qdrant`` + ``langchain`` to
    query the live vector store with the embedding model inherited from EKIE.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_WORKERS__", extra="ignore")

    connector: Literal["inmemory", "qdrant"] = "inmemory"
    query_embedder: Literal["local_hash", "langchain"] = "local_hash"
    local_embedding_dimension: int = Field(default=256, gt=0)


class FusionSettings(BaseSettings):
    """Candidate collection and fusion settings (handbook Chapters 23-24).

    Fusion is deterministic and explainable: candidates that refer to the same
    knowledge asset are grouped by the identity policy and combined with
    Reciprocal Rank Fusion. Fusion never ranks or discards information.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_FUSION__", extra="ignore")

    identity_policy: Literal["chunk", "document", "strict"] = "chunk"
    rrf_k: int = Field(default=60, gt=0)


class RankingSettings(BaseSettings):
    """Ranking engine settings (handbook Chapter 25).

    Ranking is deterministic, auditable, and evidence-driven. Evidence weights,
    the candidate limit, and the score threshold are configurable; the optional
    cross-encoder reranker is feature-flagged and always degrades to the
    deterministic ordering, so ranking stays reproducible.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_RANKING__", extra="ignore")

    candidate_limit: int = Field(default=10, gt=0)
    min_composite_score: float = Field(default=0.0, ge=0.0)
    semantic_weight: float = Field(default=0.4, ge=0.0)
    lexical_weight: float = Field(default=0.2, ge=0.0)
    metadata_weight: float = Field(default=0.1, ge=0.0)
    fusion_weight: float = Field(default=0.3, ge=0.0)
    policy_version: str = "v1"
    # Cross-encoder reranker (handbook Chapter 25.11): a purpose-built reranker
    # model (for example Qwen/Qwen3-VL-Reranker-2B) scores query/document
    # relevance and reorders the top candidates. It performs no chat generation
    # (that is EKCP). Disabled by default; when enabled it degrades gracefully to
    # the deterministic ordering. Device/precision mirror the query embedder.
    enable_reranker: bool = False
    reranker_model: str = ""
    reranker_device: str = "auto"
    reranker_torch_dtype: str = "auto"
    reranker_trust_remote_code: bool = False

    def weights(self) -> dict[str, float]:
        """Return the evidence factor weights keyed by factor name."""
        return {
            "semantic": self.semantic_weight,
            "lexical": self.lexical_weight,
            "metadata": self.metadata_weight,
            "fusion": self.fusion_weight,
        }


class AssemblySettings(BaseSettings):
    """Context assembly and response packaging settings (handbook Ch.26-27).

    Assembly selects and organizes ranked knowledge within a token budget and
    packages the citation-preserving Retrieval Context Package handed to EKCP.
    Citation lineage is never dropped. All values are configuration-driven.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_ASSEMBLY__", extra="ignore")

    max_context_tokens: int = Field(default=4000, gt=0)
    max_objects: int = Field(default=10, gt=0)
    ordering: Literal["rank", "document"] = "rank"
    normalize_whitespace: bool = True
    dedupe_content: bool = True
    chars_per_token: int = Field(default=4, gt=0)
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)


class GovernanceSettings(BaseSettings):
    """Observability, security audit, and compliance settings (Ch.28-29).

    Cross-cutting hardening: every query is traced with a latency breakdown,
    every retrieval authorization decision is audited to an immutable trail, and
    sensitive content is masked before the EKCP handoff. All policy-driven.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_GOVERNANCE__", extra="ignore")

    enable_audit: bool = True
    audit_sink: Literal["logging", "memory"] = "logging"
    enable_masking: bool = True
    mask_email: bool = True
    mask_phone: bool = True
    mask_ssn: bool = True
    mask_credit_card: bool = True
    total_latency_budget_ms: float = Field(default=500.0, gt=0.0)
    policy_version: str = "v1"


class DeploymentSettings(BaseSettings):
    """Deployment, scalability, resilience, and NFR-validation settings (Ch.30, Ch.5).

    Deployment topology is separate from business logic; these values tune
    worker-pool sizing, resilience (circuit breaker), multi-tenant admission, and
    the accuracy/latency thresholds validated for EKCP handoff readiness.
    """

    model_config = SettingsConfigDict(env_prefix="EKRE_DEPLOYMENT__", extra="ignore")

    vector_pool_size: int = Field(default=4, gt=0)
    keyword_pool_size: int = Field(default=2, gt=0)
    metadata_pool_size: int = Field(default=2, gt=0)
    replicas: int = Field(default=2, gt=0)
    circuit_breaker_threshold: int = Field(default=5, gt=0)
    circuit_breaker_reset_seconds: float = Field(default=30.0, gt=0.0)
    tenant_max_concurrent: int = Field(default=8, ge=0)
    max_latency_ms: float = Field(default=500.0, gt=0.0)
    min_availability: float = Field(default=0.999, ge=0.0, le=1.0)
    eval_k: int = Field(default=10, gt=0)
    min_precision_at_k: float = Field(default=0.5, ge=0.0, le=1.0)
    min_recall_at_k: float = Field(default=0.5, ge=0.0, le=1.0)
    min_mrr: float = Field(default=0.5, ge=0.0, le=1.0)
    min_ndcg: float = Field(default=0.5, ge=0.0, le=1.0)









class EkreSettings(BaseSettings):
    """Top-level EKRE settings composed of engine subsystem settings."""

    model_config = SettingsConfigDict(
        env_prefix="EKRE_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "ekre"
    environment: str = "local"

    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    inheritance: InheritanceSettings = Field(default_factory=InheritanceSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    query: QueryIntelligenceSettings = Field(default_factory=QueryIntelligenceSettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    workers: WorkerSettings = Field(default_factory=WorkerSettings)
    fusion: FusionSettings = Field(default_factory=FusionSettings)
    ranking: RankingSettings = Field(default_factory=RankingSettings)
    assembly: AssemblySettings = Field(default_factory=AssemblySettings)
    governance: GovernanceSettings = Field(default_factory=GovernanceSettings)
    deployment: DeploymentSettings = Field(default_factory=DeploymentSettings)



@lru_cache(maxsize=1)
def get_settings() -> EkreSettings:
    """Return a cached, process-wide EKRE settings instance."""
    return EkreSettings()
