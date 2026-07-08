"""Tests for PII masking (compliance)."""

from __future__ import annotations

from contracts.retrieval import Citation, RetrievalCandidate, RetrievalContextPackage
from domain.governance import Masker, MaskingConfig


def _candidate(content: str) -> RetrievalCandidate:
    return RetrievalCandidate(
        citation=Citation(document_id="d1", chunk_id="c1", source_path="/docs/d1.md"),
        content=content,
        relevance_score=0.9,
        explanation=None,
    )


def test_masks_email_and_ssn() -> None:
    masker = Masker(MaskingConfig())
    masked, count = masker.mask_text("Contact john@acme.com or SSN 123-45-6789.")
    assert "[REDACTED-EMAIL]" in masked
    assert "[REDACTED-SSN]" in masked
    assert "john@acme.com" not in masked
    assert count == 2


def test_masking_disabled_is_noop() -> None:
    masker = Masker(MaskingConfig(enabled=False))
    masked, count = masker.mask_text("john@acme.com")
    assert masked == "john@acme.com"
    assert count == 0


def test_masks_luhn_valid_card_only() -> None:
    # Isolate the credit-card matcher (the phone matcher can also match digit runs).
    masker = Masker(MaskingConfig(email=False, ssn=False, phone=False))
    # 4242 4242 4242 4242 is Luhn-valid; the 16-digit sequence below is not.
    masked, count = masker.mask_text("card 4242 4242 4242 4242 not 1234 5678 9012 3456")
    assert "[REDACTED-CARD]" in masked
    assert "4242 4242 4242 4242" not in masked
    assert "1234 5678 9012 3456" in masked
    assert count == 1


def test_mask_package_preserves_citation() -> None:
    package = RetrievalContextPackage(
        query="q",
        tenant_id="tenant-a",
        candidates=[_candidate("reach me at jane@acme.com")],
        security_filtered=True,
    )
    masked_package, count = Masker(MaskingConfig()).mask_package(package)
    assert count == 1
    candidate = masked_package.candidates[0]
    assert "[REDACTED-EMAIL]" in candidate.content
    # Citation lineage is never altered by masking.
    assert candidate.citation.document_id == "d1"
    assert candidate.citation.source_path == "/docs/d1.md"


def test_mask_package_without_pii_is_unchanged() -> None:
    package = RetrievalContextPackage(
        query="q",
        tenant_id="tenant-a",
        candidates=[_candidate("no sensitive content here")],
        security_filtered=True,
    )
    masked_package, count = Masker(MaskingConfig()).mask_package(package)
    assert count == 0
    assert masked_package.candidates[0].content == "no sensitive content here"
