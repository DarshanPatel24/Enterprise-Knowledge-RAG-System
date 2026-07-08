"""Sensitive-data masking (handbook Chapters 29.10).

Best-effort redaction of common PII patterns from candidate content before the
EKCP handoff, as a defense-in-depth control (not a completeness guarantee):
pattern-based detection cannot catch every form of sensitive data (names,
addresses, international formats, tokens split across chunks). Authorization and
tenant/clearance filtering remain the primary controls. Masking is deterministic
and configurable; citation lineage is always preserved (only content is masked).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from contracts.retrieval import RetrievalCandidate, RetrievalContextPackage

# Order matters: SSN before the broad credit-card pattern so it is not swallowed.
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
_CREDIT_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")


def _luhn_valid(digits: str) -> bool:
    """Return whether ``digits`` satisfies the Luhn checksum (card-number check)."""
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = ord(char) - 48
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _mask_credit_cards(text: str) -> tuple[str, int]:
    """Redact only Luhn-valid card numbers, reducing false positives."""
    count = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal count
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 16 and _luhn_valid(digits):
            count += 1
            return "[REDACTED-CARD]"
        return match.group(0)

    return _CREDIT_CARD.sub(_replace, text), count


@dataclass(frozen=True)
class MaskingConfig:
    """Which PII categories to mask."""

    enabled: bool = True
    email: bool = True
    phone: bool = True
    ssn: bool = True
    credit_card: bool = True


class Masker:
    """Deterministic best-effort PII masker for retrieval content."""

    def __init__(self, config: MaskingConfig) -> None:
        self._config = config

    def mask_text(self, text: str) -> tuple[str, int]:
        """Return the masked text and the number of redactions applied."""
        if not self._config.enabled:
            return text, 0
        masked = text
        count = 0
        # SSN and email first; phone before credit-card to avoid overlap.
        if self._config.email:
            masked, hits = _EMAIL.subn("[REDACTED-EMAIL]", masked)
            count += hits
        if self._config.ssn:
            masked, hits = _SSN.subn("[REDACTED-SSN]", masked)
            count += hits
        if self._config.phone:
            masked, hits = _PHONE.subn("[REDACTED-PHONE]", masked)
            count += hits
        if self._config.credit_card:
            masked, hits = _mask_credit_cards(masked)
            count += hits
        return masked, count

    def mask_candidate(self, candidate: RetrievalCandidate) -> tuple[RetrievalCandidate, int]:
        """Return a candidate with masked content, preserving its citation."""
        masked_content, count = self.mask_text(candidate.content)
        if count == 0:
            return candidate, 0
        return candidate.model_copy(update={"content": masked_content}), count

    def mask_package(
        self, package: RetrievalContextPackage
    ) -> tuple[RetrievalContextPackage, int]:
        """Return the package with masked candidate content and the redaction count."""
        if not self._config.enabled:
            return package, 0
        masked: list[RetrievalCandidate] = []
        total = 0
        for candidate in package.candidates:
            new_candidate, count = self.mask_candidate(candidate)
            masked.append(new_candidate)
            total += count
        if total == 0:
            return package, 0
        return package.model_copy(update={"candidates": masked}), total


def redaction_count(masker: Masker, texts: Sequence[str]) -> int:
    """Return the total redactions the masker would apply to ``texts``."""
    return sum(masker.mask_text(text)[1] for text in texts)
