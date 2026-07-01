"""Tests for normalization, canonical Markdown, and validation."""

from domain.transformation import (
    FrontMatter,
    MarkdownDocument,
    MarkdownValidator,
    normalize_text,
)


def test_normalize_converts_newlines_and_trims() -> None:
    result = normalize_text("a  \r\nb\r\n\r\n\r\nc")
    assert result == "a\nb\n\nc\n"


def test_normalize_removes_control_characters() -> None:
    result = normalize_text("clean\x00text\x07here")
    assert result == "cleantexthere\n"


def test_normalize_is_deterministic_for_unicode() -> None:
    decomposed = "e\u0301"  # e + combining acute accent
    composed = "\u00e9"  # precomposed e-acute
    assert normalize_text(decomposed) == normalize_text(composed)


def test_front_matter_renders_ordered_yaml() -> None:
    front = FrontMatter(
        document_id="DOC-1",
        repository_id="REP-1",
        version=3,
        source_type="txt",
        source_hash="sha256:abc",
        language="en",
        title="My Doc",
    )
    rendered = front.render()
    assert rendered.startswith("---\ndocument_id: DOC-1\n")
    assert "version: 3" in rendered
    assert rendered.endswith("---")


def test_markdown_document_renders_front_matter_and_body() -> None:
    front = FrontMatter(
        document_id="DOC-1",
        repository_id="REP-1",
        version=1,
        source_type="txt",
        source_hash="sha256:abc",
        language="en",
    )
    doc = MarkdownDocument(body="# Title\n\nContent", front_matter=front)
    rendered = doc.render()
    assert "---" in rendered
    assert rendered.endswith("# Title\n\nContent\n")


def test_yaml_scalar_quotes_values_with_special_characters() -> None:
    front = FrontMatter(
        document_id="DOC-1",
        repository_id="REP-1",
        version=1,
        source_type="txt",
        source_hash="sha256:abc",
        language="en",
        title="Plan: Q3",
    )
    assert 'title: "Plan: Q3"' in front.render()


def test_validator_flags_empty_document() -> None:
    report = MarkdownValidator().validate(MarkdownDocument(body="", front_matter=None))
    assert not report.is_valid
    assert "empty content" in report.errors


def test_validator_flags_missing_required_metadata() -> None:
    front = FrontMatter(
        document_id="",
        repository_id="REP-1",
        version=1,
        source_type="txt",
        source_hash="sha256:abc",
        language="en",
    )
    report = MarkdownValidator().validate(MarkdownDocument(body="content", front_matter=front))
    assert not report.is_valid
    assert any("document_id" in error for error in report.errors)


def test_validator_accepts_complete_document() -> None:
    front = FrontMatter(
        document_id="DOC-1",
        repository_id="REP-1",
        version=1,
        source_type="txt",
        source_hash="sha256:abc",
        language="en",
    )
    report = MarkdownValidator().validate(MarkdownDocument(body="content", front_matter=front))
    assert report.is_valid
    assert report.errors == []
