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
    derive_source_group_from_path: bool
    source_group_depth: int
    default_source_group: str


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
    # Derive a product/source group tag from each document's leading folder so
    # retrieval can be scoped by product. Depth is how many leading folders form
    # the tag; default applies to root-level documents.
    derive_source_group_from_path: bool = True
    source_group_depth: int = Field(default=1, ge=1)
    default_source_group: str = ""

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
            derive_source_group_from_path=settings.derive_source_group_from_path,
            source_group_depth=settings.source_group_depth,
            default_source_group=settings.default_source_group,
        )
