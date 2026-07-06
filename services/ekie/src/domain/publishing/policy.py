"""Publishing policy: configuration-driven provider, collection, and retry (handbook 11.11)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class PublishingSettingsLike(Protocol):
    """Structural type for environment-backed publishing settings."""

    provider: str
    default_collection: str
    collection_strategy: str
    batch_size: int
    max_retries: int
    create_missing_collections: bool
    verify_after_publish: bool
    max_vectors_per_minute: int


class PublishingPolicy(BaseModel):
    """Versioned, configuration-driven publishing behavior (ADR-025).

    Collection names are resolved from policy rather than hardcoded in code
    (handbook 11.11). Publishing is verified by default (ADR-026).
    """

    model_config = {"frozen": True}

    provider: str = "local"
    default_collection: str = "enterprise_documents"
    collection_strategy: str = "static"
    batch_size: int = Field(default=64, gt=0)
    max_retries: int = Field(default=3, ge=0)
    create_missing_collections: bool = True
    verify_after_publish: bool = True
    max_vectors_per_minute: int = Field(default=0, ge=0)

    @classmethod
    def from_settings(cls, settings: PublishingSettingsLike) -> PublishingPolicy:
        """Build a policy from environment-backed publishing settings."""
        return cls(
            provider=settings.provider,
            default_collection=settings.default_collection,
            collection_strategy=settings.collection_strategy,
            batch_size=settings.batch_size,
            max_retries=settings.max_retries,
            create_missing_collections=settings.create_missing_collections,
            verify_after_publish=settings.verify_after_publish,
            max_vectors_per_minute=settings.max_vectors_per_minute,
        )
