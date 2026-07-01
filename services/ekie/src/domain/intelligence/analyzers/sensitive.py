"""Sensitive content detection analyzer (handbook 8.12).

Scans for governance-relevant content and reports aggregated findings only.
Detected content is never modified; the framework produces metadata for
downstream governance workflows.
"""

from __future__ import annotations

import re
from typing import ClassVar

from domain.intelligence.analysis import AnalyzedDocument
from domain.intelligence.analyzers.base import Analyzer, IntelligenceReportBuilder
from domain.intelligence.models import SensitiveContentType, SensitiveFinding
from domain.intelligence.policy import IntelligencePolicy

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{8,}\d(?!\w)")
_CREDIT_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_NATIONAL_ID = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_API_KEY = re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token)\b\s*[:=]\s*\S+")
_SECRET = re.compile(r"(?i)\b(?:password|passwd|secret|client[_-]?secret)\b\s*[:=]\s*\S+")


def _luhn_valid(digits: str) -> bool:
    numbers = [int(char) for char in digits if char.isdigit()]
    if not 13 <= len(numbers) <= 19:
        return False
    checksum = 0
    parity = len(numbers) % 2
    for index, digit in enumerate(numbers):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


class SensitiveContentAnalyzer(Analyzer):
    """Flags emails, phone numbers, secrets, and identifiers for governance."""

    name: ClassVar[str] = "sensitive_content"

    def analyze(
        self,
        document: AnalyzedDocument,
        builder: IntelligenceReportBuilder,
        policy: IntelligencePolicy,
    ) -> None:
        """Aggregate sensitive-content findings without modifying content."""
        if not policy.detect_sensitive_content:
            return
        text = "\n".join(block.text for block in document.blocks)

        counts: dict[SensitiveContentType, int] = {
            SensitiveContentType.EMAIL_ADDRESS: len(_EMAIL.findall(text)),
            SensitiveContentType.PHONE_NUMBER: len(_PHONE.findall(text)),
            SensitiveContentType.CREDIT_CARD: sum(
                1 for match in _CREDIT_CARD.findall(text) if _luhn_valid(match)
            ),
            SensitiveContentType.NATIONAL_ID: len(_NATIONAL_ID.findall(text)),
            SensitiveContentType.API_KEY: len(_API_KEY.findall(text)),
            SensitiveContentType.SECRET: len(_SECRET.findall(text)),
        }
        for finding_type, count in counts.items():
            if count > 0:
                builder.sensitive_findings.append(
                    SensitiveFinding(finding_type=finding_type, count=count)
                )
