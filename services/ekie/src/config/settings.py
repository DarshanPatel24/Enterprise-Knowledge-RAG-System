"""Environment-backed configuration for the EKIE service.

All operational values are configuration-driven (configuration over code).
No credentials, endpoints, or limits are hardcoded; values load from the
process environment or a local ``.env`` file with the ``EKIE_`` prefix.
"""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ControlPlaneSettings(BaseSettings):
    """Microsoft SQL Server control-plane connection settings.

    A full SQLAlchemy URL may be supplied via ``EKIE_CONTROL_PLANE__URL`` to
    override component-based construction (for example a local SQLite URL used
    in tests). When absent, the URL is built from the MS SQL components.
    """

    model_config = SettingsConfigDict(env_prefix="EKIE_CONTROL_PLANE__", extra="ignore")

    url: str | None = None
    host: str = "localhost"
    port: int = 1433
    database: str = "ekrag_control_plane"
    user: str = "sa"
    password: str = ""
    driver: str = "ODBC Driver 18 for SQL Server"
    trust_server_certificate: bool = True
    encrypt: bool = True

    def sqlalchemy_url(self) -> str:
        """Return the SQLAlchemy connection URL for the control plane."""
        if self.url:
            return self.url
        query = (
            f"driver={quote_plus(self.driver)}"
            f"&Encrypt={'yes' if self.encrypt else 'no'}"
            f"&TrustServerCertificate={'yes' if self.trust_server_certificate else 'no'}"
        )
        return (
            f"mssql+pyodbc://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.database}?{query}"
        )


class QdrantSettings(BaseSettings):
    """Qdrant vector database connection settings."""

    model_config = SettingsConfigDict(env_prefix="EKIE_QDRANT__", extra="ignore")

    host: str = "localhost"
    port: int = 6333
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
    image_handling: str = "reference"
    ocr_enabled: bool = False


class IntelligenceSettings(BaseSettings):
    """Environment-backed defaults for the document intelligence policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_INTELLIGENCE__", extra="ignore")

    detect_language: bool = True
    classify_content: bool = True
    detect_sensitive_content: bool = True
    default_language: str = "en"
    high_complexity_section_threshold: int = 12
    enable_llm_analysis: bool = False
    llm_provider: str = "ollama"
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


class EmbeddingSettings(BaseSettings):
    """Environment-backed defaults for the embedding framework policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_EMBEDDING__", extra="ignore")

    default_model: str = "local-hash-256"
    provider: str = "local"
    dimension: int = 256
    distance_metric: str = "cosine"
    max_input_tokens: int = 8192
    batch_size: int = 16
    normalize_vectors: bool = True
    cost_per_1k_tokens: float = 0.0
    max_retries: int = 3
    ollama_base_url: str = "http://localhost:11434"
    request_timeout_seconds: float = 60.0


class PublishingSettings(BaseSettings):
    """Environment-backed defaults for the vector publishing policy."""

    model_config = SettingsConfigDict(env_prefix="EKIE_PUBLISHING__", extra="ignore")

    provider: str = "local"
    default_collection: str = "enterprise_documents"
    batch_size: int = 64
    max_retries: int = 3
    create_missing_collections: bool = True
    verify_after_publish: bool = True


class EkieSettings(BaseSettings):
    """Top-level EKIE settings composed of engine subsystem settings."""

    model_config = SettingsConfigDict(
        env_prefix="EKIE_",
        env_file=".env",
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


@lru_cache(maxsize=1)
def get_settings() -> EkieSettings:
    """Return a cached, process-wide EKIE settings instance."""
    return EkieSettings()
