"""Unit tests for chunk validation rules."""

from domain.chunking import ChunkingPolicy, ChunkValidator
from domain.chunking.strategies.base import ChunkDraft
from domain.chunking.validation import ChunkValidationErrorType


def _draft(**overrides: object) -> ChunkDraft:
    defaults: dict[str, object] = {
        "section_id": "SEC-1",
        "section_title": "Safety",
        "breadcrumb": "Doc > Safety",
        "heading_level": 2,
        "content": "> Context: Doc > Safety\n\nSome content.",
        "token_count": 20,
        "contains_table": False,
        "contains_code": False,
        "contains_image": False,
    }
    defaults.update(overrides)
    return ChunkDraft(**defaults)  # type: ignore[arg-type]


def test_valid_draft_passes() -> None:
    validator = ChunkValidator(ChunkingPolicy())
    report = validator.validate(_draft(), {"SEC-1"})
    assert report.valid is True
    assert report.errors == []


def test_empty_content_rejected() -> None:
    validator = ChunkValidator(ChunkingPolicy())
    report = validator.validate(_draft(content="   "), {"SEC-1"})
    assert ChunkValidationErrorType.EMPTY_CONTENT in report.errors


def test_missing_metadata_rejected() -> None:
    validator = ChunkValidator(ChunkingPolicy())
    report = validator.validate(_draft(section_title="", breadcrumb=""), {"SEC-1"})
    assert ChunkValidationErrorType.MISSING_METADATA in report.errors


def test_broken_hierarchy_rejected() -> None:
    validator = ChunkValidator(ChunkingPolicy())
    report = validator.validate(_draft(section_id="SEC-9"), {"SEC-1"})
    assert ChunkValidationErrorType.BROKEN_HIERARCHY in report.errors


def test_preamble_section_id_none_is_allowed() -> None:
    validator = ChunkValidator(ChunkingPolicy())
    report = validator.validate(_draft(section_id=None), {"SEC-1"})
    assert report.valid is True


def test_exceeds_budget_rejected_for_flowing_content() -> None:
    validator = ChunkValidator(ChunkingPolicy(max_token_budget=10))
    report = validator.validate(_draft(token_count=50), {"SEC-1"})
    assert ChunkValidationErrorType.EXCEEDS_TOKEN_BUDGET in report.errors


def test_exceeds_budget_allowed_for_preserved_table() -> None:
    validator = ChunkValidator(ChunkingPolicy(max_token_budget=10))
    report = validator.validate(
        _draft(token_count=50, contains_table=True), {"SEC-1"}
    )
    assert report.valid is True
