"""Chunk validation rules (handbook 9.18)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from domain.chunking.policy import ChunkingPolicy
from domain.chunking.strategies.base import ChunkDraft


class ChunkValidationErrorType(StrEnum):
    """Categories of chunk validation failure (handbook 9.18)."""

    EMPTY_CONTENT = "empty_content"
    MISSING_METADATA = "missing_metadata"
    BROKEN_HIERARCHY = "broken_hierarchy"
    EXCEEDS_TOKEN_BUDGET = "exceeds_token_budget"  # noqa: S105 - label, not a credential


@dataclass(frozen=True)
class ChunkValidationReport:
    """The outcome of validating a single chunk draft."""

    valid: bool
    errors: list[ChunkValidationErrorType] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


class ChunkValidator:
    """Applies deterministic validation rules to generated chunk drafts."""

    def __init__(self, policy: ChunkingPolicy) -> None:
        self._policy = policy

    def validate(
        self, draft: ChunkDraft, known_section_ids: set[str]
    ) -> ChunkValidationReport:
        """Validate a chunk draft against structural and budget rules."""
        errors: list[ChunkValidationErrorType] = []
        messages: list[str] = []

        if not draft.content.strip():
            errors.append(ChunkValidationErrorType.EMPTY_CONTENT)
            messages.append("chunk content is empty")

        if not draft.section_title.strip() or not draft.breadcrumb.strip():
            errors.append(ChunkValidationErrorType.MISSING_METADATA)
            messages.append("chunk is missing section title or breadcrumb")

        if draft.section_id is not None and draft.section_id not in known_section_ids:
            errors.append(ChunkValidationErrorType.BROKEN_HIERARCHY)
            messages.append(f"section {draft.section_id!r} is not in the structure tree")

        preserved_atomic = draft.contains_table or draft.contains_code
        if draft.token_count > self._policy.max_token_budget and not preserved_atomic:
            errors.append(ChunkValidationErrorType.EXCEEDS_TOKEN_BUDGET)
            messages.append(
                f"chunk has {draft.token_count} tokens; max is "
                f"{self._policy.max_token_budget}"
            )

        return ChunkValidationReport(valid=not errors, errors=errors, messages=messages)
