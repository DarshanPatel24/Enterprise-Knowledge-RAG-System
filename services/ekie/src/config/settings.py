"""Environment-backed configuration for the EKIE service.

All operational values are configuration-driven (configuration over code).
No credentials, endpoints, or limits are hardcoded; values load from the
process environment or a local ``.env`` file with the ``EKIE_`` prefix.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the .env file co-located with services/ekie/ regardless of
# the process working directory. Using an absolute path prevents silent settings
# fall-through when uvicorn or scripts are started from the repository root.
# Path hierarchy from this file (services/ekie/src/config/settings.py):
#   parents[0] = config/
#   parents[1] = src/
#   parents[2] = services/ekie/   <-- .env lives here
_ENV_FILE = str(Path(__file__).resolve().parents[2] / ".env")


class ControlPlaneSettings(BaseSettings):
    """Microsoft SQL Server control-plane connection settings.

    A full SQLAlchemy URL may be supplied via ``EKIE_CONTROL_PLANE__URL`` to
    override component-based construction (for example a local SQLite URL used
    in tests). When absent, the URL is built from the MS SQL components.
    """

    model_config = SettingsConfigDict(env_prefix="EKIE_CONTROL_PLANE__", extra="ignore")

    url: str | None = None
    host: str = "localhost"
    port: int | str | None = 1433
    database: str = "ekrag_control_plane"
    user: str = "sa"
    password: str = ""
    driver: str = "ODBC Driver 18 for SQL Server"
    trust_server_certificate: bool = True
    encrypt: bool = True
    trusted_connection: bool = False

    def sqlalchemy_url(self) -> str:
        """Return the SQLAlchemy connection URL for the control plane."""
        if self.url:
            return self.url
        query = (
            f"driver={quote_plus(self.driver)}"
            f"&Encrypt={'yes' if self.encrypt else 'no'}"
            f"&TrustServerCertificate={'yes' if self.trust_server_certificate else 'no'}"
        )
        
        if self.trusted_connection:
            query += "&Trusted_Connection=yes"
            auth = ""
        elif self.user or self.password:
            auth = f"{quote_plus(self.user)}:{quote_plus(self.password)}@"
        else:
            auth = ""

        actual_port = None if self.port == "" else self.port
        port_str = f":{actual_port}" if actual_port is not None else ""

        return (
            f"mssql+pyodbc://{auth}"
            f"{self.host}{port_str}/{self.database}?{query}"
        )


class QdrantSettings(BaseSettings):
    """Qdrant vector database connection settings."""

    model_config = SettingsConfigDict(env_prefix="EKIE_QDRANT__", extra="ignore")

    host: str = "localhost"
    port: int = 6333
    url: str = ""
    api_key: str = ""
    request_timeout_seconds: float = 30.0


class RedisSettings(BaseSettings):
    """Redis cache connection settings."""

    model_config = SettingsConfigDict(env_prefix="EKIE_REDIS__", extra="ignore")

    host: str = "localhost"
    port: int = 6379


class StorageSettings(BaseSettings):
    """MinIO-backed object storage settings for immutable versioned assets."""

    model_config = SettingsConfigDict(env_prefix="EKIE_STORAGE__", extra="ignore")

    endpoint: str = "localhost:9000"
    access_key: str = ""
    secret_key: str = ""
    bucket: str = "ekie-assets"
    secure: bool = False
    # Local-first persistent asset directory used when MinIO is not configured
    # (the default local environment). Stage payloads are written here so they
    # survive API/worker restarts; resolved relative to the service working
    # directory. Kept out of memory to avoid losing assets on restart.
    local_path: str = "storage/assets"


class ObservabilitySettings(BaseSettings):
    """Observability settings for logging, tracing, and Langfuse."""

    model_config = SettingsConfigDict(env_prefix="EKIE_OBSERVABILITY__", extra="ignore")

    log_level: str = "INFO"
    service_name: str = "ekie"
    langfuse_enabled: bool = False
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    otel_exporter_endpoint: str | None = None


class SyncSettings(BaseSettings):
    """Environment-backed defaults for the repository synchronization policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_SYNC__", extra="ignore")

    scan_strategy: str = "incremental"
    ignore_hidden: bool = True
    ignore_temp: bool = True
    max_file_size_bytes: int = 524_288_000
    allowed_extensions: str = ""
    hash_algorithm: str = "sha256"
    rename_detection_enabled: bool = True
    delete_propagation_enabled: bool = True
    default_classification: str = "internal"

    # Built-in production worker settings
    target_directory: str = ""
    tenant_id: str = "tenant-default"
    poll_interval_seconds: int = 300
    api_base_url: str = "http://localhost:8001"
    ingest_timeout_seconds: float = 1800.0
    delete_timeout_seconds: float = 120.0

    def parsed_extensions(self) -> frozenset[str]:
        """Return the allowed extensions as a normalized set (empty means all)."""
        return frozenset(
            item.strip().lower().lstrip(".")
            for item in self.allowed_extensions.split(",")
            if item.strip()
        )


class TransformationSettings(BaseSettings):
    """Environment-backed defaults for the document transformation policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_TRANSFORMATION__", extra="ignore")

    normalize_unicode: bool = True
    collapse_blank_lines: bool = True
    include_front_matter: bool = True
    default_language: str = "en"


class IntelligenceSettings(BaseSettings):
    """Environment-backed defaults for the document intelligence policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_INTELLIGENCE__", extra="ignore")

    detect_language: bool = True
    classify_content: bool = True
    detect_sensitive_content: bool = True
    default_language: str = "en"
    high_complexity_section_threshold: int = 12
    enable_llm_analysis: bool = False
    llm_provider: Literal["ollama", "huggingface"] = "ollama"
    llm_model: str = "llama3.1"
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.0
    llm_request_timeout_seconds: float = 60.0


class ChunkingSettings(BaseSettings):
    """Environment-backed defaults for the intelligent chunking policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_CHUNKING__", extra="ignore")

    default_strategy: str = "semantic"
    target_token_budget: int = 512
    max_token_budget: int = 1024
    min_chunk_tokens: int = 8
    preserve_tables: bool = True
    preserve_code: bool = True
    respect_section_boundaries: bool = True
    include_breadcrumb_context: bool = True
    recursive_chunk_size: int = 1000
    recursive_chunk_overlap: int = 200


class EmbeddingSettings(BaseSettings):
    """Environment-backed defaults for the embedding framework policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_EMBEDDING__", extra="ignore")

    default_model: str = "local-hash-256"
    provider: Literal["local", "ollama", "huggingface"] = "local"
    dimension: int = Field(default=256, gt=0)
    distance_metric: Literal["cosine", "dot_product", "euclidean"] = "cosine"
    max_input_tokens: int = 8192
    batch_size: int = 16
    normalize_vectors: bool = True
    cost_per_1k_tokens: float = 0.0
    max_retries: int = 3
    max_requests_per_minute: int = 0
    ollama_base_url: str = "http://localhost:11434"
    request_timeout_seconds: float = 60.0
    # HuggingFace provider device/precision. "auto" preserves library defaults
    # (GPU auto-detect, fp32). Set torch_dtype to "float16" to fit large models
    # on limited-VRAM GPUs; set device to "cuda"/"cpu" to force placement.
    device: str = "auto"
    torch_dtype: str = "auto"


class PublishingSettings(BaseSettings):
    """Environment-backed defaults for the vector publishing policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_PUBLISHING__", extra="ignore")

    provider: Literal["local", "qdrant"] = "local"
    default_collection: str = "enterprise_documents"
    collection_strategy: Literal["static", "model_scoped"] = "static"
    batch_size: int = 64
    max_retries: int = 3
    max_vectors_per_minute: int = 0
    create_missing_collections: bool = True
    verify_after_publish: bool = True


class OrchestrationSettings(BaseSettings):
    """Environment-backed defaults for the ingestion workflow orchestrator."""

    model_config = SettingsConfigDict(env_prefix="EKIE_ORCHESTRATION__", extra="ignore")

    runner: str = "sequential"
    max_attempts_per_stage: int = 3
    retry_backoff_base_seconds: float = 0.0
    retry_backoff_multiplier: float = 2.0
    enable_tracing: bool = False


class IngestionSettings(BaseSettings):
    """Environment-backed defaults for the durable, queue-backed ingestion path.

    When ``async_enabled`` is true the ingestion API enqueues a durable job and
    returns immediately, and a separate worker pool executes the pipeline. This
    decouples request latency from pipeline duration so large documents no longer
    exhaust HTTP timeouts. All values are operational tunables so throughput and
    retry behavior can be adjusted without code changes.
    """

    model_config = SettingsConfigDict(env_prefix="EKIE_INGESTION__", extra="ignore")

    async_enabled: bool = False
    worker_concurrency: int = 1
    claim_batch_size: int = 1
    poll_interval_seconds: float = 2.0
    max_attempts: int = 3
    retry_backoff_base_seconds: float = 30.0
    retry_backoff_multiplier: float = 2.0
    retry_backoff_max_seconds: float = 900.0
    # A running worker refreshes its job lock every ``heartbeat_interval_seconds``.
    # A job is treated as orphaned (and reclaimed for resume) once its lock has
    # not been refreshed for ``visibility_timeout_seconds``. Keep the timeout a
    # comfortable multiple of the interval so a live worker is never reclaimed,
    # while a crashed worker's job resumes within roughly the timeout window.
    heartbeat_interval_seconds: float = 15.0
    visibility_timeout_seconds: float = 90.0


class SecuritySettings(BaseSettings):
    """Environment-backed defaults for authentication and authorization.

    Local-first defaults keep the offline path open: when authentication is
    disabled the service authenticates a configured anonymous principal so the
    pipeline runs without external identity infrastructure, while production
    deployments enable API-key authentication and per-stage enforcement.
    """

    model_config = SettingsConfigDict(env_prefix="EKIE_SECURITY__", extra="ignore")

    require_authentication: bool = False
    enforce_authorization: bool = True
    anonymous_role: str = "service_worker"
    anonymous_clearance: str = "restricted"
    minimum_clearance: str = "public"


class GovernanceSettings(BaseSettings):
    """Environment-backed defaults for audit logging and classification policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_GOVERNANCE__", extra="ignore")

    enable_audit: bool = True
    audit_sink: str = "logging"
    allow_classification_downgrade: bool = False


class PluginSettings(BaseSettings):
    """Environment-backed defaults for plugin activation and sandbox validation."""

    model_config = SettingsConfigDict(env_prefix="EKIE_PLUGINS__", extra="ignore")

    require_signature: bool = True
    allow_unsigned: bool = False
    trusted_publishers: str = ""
    ekie_version: str = "1.0.0"
    sandbox_timeout_seconds: float = 5.0

    def parsed_trusted_publishers(self) -> frozenset[str]:
        """Return the configured trusted publisher identities as a set."""
        return frozenset(
            item.strip()
            for item in self.trusted_publishers.split(",")
            if item.strip()
        )


class DeploymentSettings(BaseSettings):
    """Deployment, non-functional, and disaster-recovery target settings.

    Encodes the readiness targets validated in EKIE-S9: pipeline success rate,
    per-stage latency budget, and disaster-recovery RPO/RTO objectives. Values
    are configuration-driven so readiness criteria can vary per environment.
    """

    model_config = SettingsConfigDict(env_prefix="EKIE_DEPLOYMENT__", extra="ignore")

    min_success_rate: float = 0.99
    max_stage_latency_seconds: float = 5.0
    rpo_seconds: float = 300.0
    rto_seconds: float = 900.0
    replicas: int = 1


class EkieSettings(BaseSettings):
    """Top-level EKIE settings composed of engine subsystem settings."""

    model_config = SettingsConfigDict(
        env_prefix="EKIE_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "ekie"
    environment: str = "local"

    control_plane: ControlPlaneSettings = Field(default_factory=ControlPlaneSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    sync: SyncSettings = Field(default_factory=SyncSettings)
    transformation: TransformationSettings = Field(default_factory=TransformationSettings)
    intelligence: IntelligenceSettings = Field(default_factory=IntelligenceSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    publishing: PublishingSettings = Field(default_factory=PublishingSettings)
    orchestration: OrchestrationSettings = Field(default_factory=OrchestrationSettings)
    ingestion: IngestionSettings = Field(default_factory=IngestionSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    governance: GovernanceSettings = Field(default_factory=GovernanceSettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    deployment: DeploymentSettings = Field(default_factory=DeploymentSettings)


@lru_cache(maxsize=1)
def get_settings() -> EkieSettings:
    """Return a cached, process-wide EKIE settings instance."""
    return EkieSettings()
