"""Markdown asset validation framework (handbook 7.15)."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.transformation.markdown_document import MarkdownDocument


class ValidationError(RuntimeError):
    """Raised when a Markdown asset fails validation before publication."""


@dataclass(frozen=True)
class ValidationReport:
    """Outcome of validating a generated Markdown document."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


class MarkdownValidator:
    """Validates canonical Markdown documents prior to storage."""

    def validate(self, document: MarkdownDocument) -> ValidationReport:
        """Return a report describing any validation failures for ``document``."""
        errors: list[str] = []
        rendered = document.render()

        if not rendered.strip():
            errors.append("empty content")

        front_matter = document.front_matter
        if front_matter is not None:
            body_present = bool(document.body.strip())
            if not body_present:
                errors.append("missing document body")
            missing = self._missing_required(front_matter)
            if missing:
                errors.append(f"missing required metadata: {', '.join(sorted(missing))}")

        try:
            rendered.encode("utf-8")
        except UnicodeEncodeError:  # pragma: no cover - str is always UTF-8 encodable
            errors.append("content is not valid UTF-8")

        return ValidationReport(is_valid=not errors, errors=errors)

    @staticmethod
    def _missing_required(front_matter: object) -> set[str]:
        required = getattr(front_matter, "required_keys", None)
        if required is None:
            return set()
        missing: set[str] = set()
        for key in required():
            value = getattr(front_matter, key, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.add(key)
        return missing
