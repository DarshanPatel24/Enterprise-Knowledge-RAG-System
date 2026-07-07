"""Readiness report primitives (advisory findings)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Severity(StrEnum):
    """Severity of a readiness finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ReadinessFinding(BaseModel):
    """A single readiness check outcome."""

    model_config = ConfigDict(frozen=True)

    check: str = Field(min_length=1)
    severity: Severity
    message: str


class ReadinessReport(BaseModel):
    """An aggregate readiness assessment; ready when there are no errors."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    findings: tuple[ReadinessFinding, ...] = ()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ready(self) -> bool:
        """Return whether the assessment passed (no ERROR findings)."""
        return not any(f.severity is Severity.ERROR for f in self.findings)

    @property
    def errors(self) -> tuple[ReadinessFinding, ...]:
        """Return the error findings."""
        return tuple(f for f in self.findings if f.severity is Severity.ERROR)


def info(check: str, message: str) -> ReadinessFinding:
    """Build an INFO finding."""
    return ReadinessFinding(check=check, severity=Severity.INFO, message=message)


def warning(check: str, message: str) -> ReadinessFinding:
    """Build a WARNING finding."""
    return ReadinessFinding(check=check, severity=Severity.WARNING, message=message)


def error(check: str, message: str) -> ReadinessFinding:
    """Build an ERROR finding."""
    return ReadinessFinding(check=check, severity=Severity.ERROR, message=message)
