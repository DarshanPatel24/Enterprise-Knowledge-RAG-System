"""Confidence scoring by validation method (handbook 8.18).

Confidence is derived deterministically from how a memory was validated. Human
confirmation is the most trusted; a raw model inference is the least. Downstream
retrieval and governance use this confidence as the trust dimension.
"""

from __future__ import annotations

from domain.memory.models import ValidationMethod

_CONFIDENCE_BY_METHOD: dict[ValidationMethod, float] = {
    ValidationMethod.USER_CONFIRMED: 0.95,
    ValidationMethod.TOOL_VERIFIED: 0.90,
    ValidationMethod.KNOWLEDGE_RETRIEVED: 0.80,
    ValidationMethod.AGENT_GENERATED: 0.75,
    ValidationMethod.LLM_INFERRED: 0.60,
}


def confidence_for(method: ValidationMethod) -> float:
    """Return the confidence score for a validation method."""
    return _CONFIDENCE_BY_METHOD[method]
