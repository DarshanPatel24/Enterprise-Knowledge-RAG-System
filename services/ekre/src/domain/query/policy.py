"""Query intelligence policy and pluggable enterprise vocabulary.

The policy is built from settings so domain engines stay independent of the
configuration module. Enterprise vocabulary (acronyms and synonyms) is injected
rather than hardcoded in engine logic; ``default_vocabulary`` provides a small,
extensible starting set following the EKIE ``default_*`` registry convention.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from domain.query.models import RetrievalProfile


class QuerySettingsLike(Protocol):
    """Structural view of the query intelligence settings the policy needs."""

    max_query_length: int
    default_language: str
    enable_llm_interpreter: bool
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_temperature: float
    llm_request_timeout_seconds: float

    def candidate_counts(self) -> dict[str, int]: ...


class EnterpriseVocabulary(BaseModel):
    """Enterprise acronym and synonym maps used by understanding and enrichment."""

    model_config = ConfigDict(frozen=True)

    acronyms: dict[str, str] = Field(default_factory=dict)
    synonyms: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    # Maps a product phrase (lowercased) found in a query to the source_group tag
    # EKIE stamped from the document folder, enabling automatic product scoping.
    products: dict[str, str] = Field(default_factory=dict)


class QueryPolicy(BaseModel):
    """Configuration-driven policy for the query intelligence pipeline."""

    model_config = ConfigDict(frozen=True)

    max_query_length: int = Field(gt=0)
    default_language: str
    candidate_counts: dict[str, int]
    enable_llm_interpreter: bool = False
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1"
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.0
    llm_request_timeout_seconds: float = 60.0

    @classmethod
    def from_settings(cls, settings: QuerySettingsLike) -> QueryPolicy:
        """Build the policy from the query intelligence settings."""
        return cls(
            max_query_length=settings.max_query_length,
            default_language=settings.default_language,
            candidate_counts=settings.candidate_counts(),
            enable_llm_interpreter=settings.enable_llm_interpreter,
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            llm_base_url=settings.llm_base_url,
            llm_temperature=settings.llm_temperature,
            llm_request_timeout_seconds=settings.llm_request_timeout_seconds,
        )

    def candidate_count(self, profile: RetrievalProfile) -> int:
        """Return the configured candidate count for a retrieval profile."""
        return self.candidate_counts.get(profile.value, self.candidate_counts["balanced"])


def default_vocabulary() -> EnterpriseVocabulary:
    """Return a small, extensible default enterprise vocabulary.

    Vocabulary is domain data, not operational configuration; operators extend
    these maps by supplying a richer :class:`EnterpriseVocabulary`.
    """
    return EnterpriseVocabulary(
        acronyms={
            "vpn": "virtual private network",
            "sso": "single sign on",
            "gdpr": "general data protection regulation",
            "kb": "knowledge base",
        },
        synonyms={
            "policy": ("guideline", "standard"),
            "guide": ("manual", "handbook"),
            "architecture": ("design", "blueprint"),
        },
    )
