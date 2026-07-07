"""Prompt orchestration models: declarative templates and the Prompt Package.

Prompts are enterprise assets constructed from ordered declarative layers with
explicit named variables; no prompt strings are hardcoded in engine logic. The
Prompt Package is the immutable, validated artifact handed to the model gateway
(EKCP-S3) for generation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PromptLayer(StrEnum):
    """Declarative prompt layers assembled in order (handbook Chapter 7)."""

    SYSTEM = "system"
    POLICY = "policy"
    CONVERSATION = "conversation"
    AGENT = "agent"
    TASK = "task"
    FORMATTING = "formatting"


class ValidationStatus(StrEnum):
    """Validation outcome of an assembled prompt package."""

    VALID = "valid"
    INVALID_VARIABLES = "invalid_variables"
    POLICY_CONFLICT = "policy_conflict"
    TOKEN_EXCEEDED = "token_exceeded"  # noqa: S105 - status label, not a secret


class PromptLayerTemplate(BaseModel):
    """Immutable single layer of a prompt template."""

    model_config = ConfigDict(frozen=True)

    layer: PromptLayer
    template: str


class PromptTemplate(BaseModel):
    """Immutable declarative prompt template with explicit input variables."""

    model_config = ConfigDict(frozen=True)

    template_id: str
    version: str = "1.0.0"
    layers: tuple[PromptLayerTemplate, ...] = ()
    required_variables: tuple[str, ...] = ()
    output_format: str = "markdown"


class PromptPackage(BaseModel):
    """Immutable, validated prompt artifact for the model gateway."""

    model_config = ConfigDict(frozen=True)

    prompt_id: str
    prompt_text: str
    template_id: str
    template_version: str
    context_id: str
    variables_used: dict[str, str] = Field(default_factory=dict)
    policy_context: tuple[str, ...] = ()
    token_estimate: int = 0
    compression_applied: bool = False
    validation_status: ValidationStatus = ValidationStatus.VALID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
