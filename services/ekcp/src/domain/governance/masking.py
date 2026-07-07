"""PII masking for responses (handbook 12; mirrors EKRE masking).

Masks personally identifiable information (email, phone, SSN, credit card) in
generated text before it leaves the platform. Masking is deterministic and
order-sensitive (email before phone so digit sequences are not partially masked).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDIT_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
_PHONE = re.compile(r"\b(?:\+?\d{1,2}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b")


class MaskingConfig(BaseModel):
    """Immutable PII masking configuration."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    email: bool = True
    phone: bool = True
    ssn: bool = True
    credit_card: bool = True


class Masker:
    """Deterministic PII masker."""

    def __init__(self, config: MaskingConfig) -> None:
        self._config = config

    def mask_text(self, text: str) -> tuple[str, int]:
        """Return the masked text and the number of redactions applied."""
        if not self._config.enabled or not text:
            return text, 0
        count = 0
        if self._config.email:
            text, n = _EMAIL.subn("[REDACTED-EMAIL]", text)
            count += n
        if self._config.ssn:
            text, n = _SSN.subn("[REDACTED-SSN]", text)
            count += n
        if self._config.credit_card:
            text, n = _CREDIT_CARD.subn("[REDACTED-CARD]", text)
            count += n
        if self._config.phone:
            text, n = _PHONE.subn("[REDACTED-PHONE]", text)
            count += n
        return text, count
