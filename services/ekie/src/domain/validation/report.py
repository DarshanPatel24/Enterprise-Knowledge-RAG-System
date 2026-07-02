"""Structured validation findings and reports (handbook Chapter 20).

A report aggregates immutable findings across checks. A report passes when it
contains no ``ERROR`` findings; warnings are advisory and do not fail a report.
Reports compose so a pipeline-level report can merge per-check sub-reports.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel


class Severity(StrEnum):
    """Severity of a validation finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationFinding(BaseModel):
    """A single immutable validation observation."""

    model_config = {"frozen": True}

    check: str
    severity: Severity
    message: str


class ValidationReport(BaseModel):
    """An aggregated, immutable result of one or more validation checks."""

    model_config = {"frozen": True}

    name: str
    findings: tuple[ValidationFinding, ...] = ()

    @property
    def passed(self) -> bool:
        """Return ``True`` when the report contains no error findings."""
        return not any(f.severity is Severity.ERROR for f in self.findings)

    @property
    def errors(self) -> tuple[ValidationFinding, ...]:
        """Return the error-severity findings."""
        return tuple(f for f in self.findings if f.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationFinding, ...]:
        """Return the warning-severity findings."""
        return tuple(f for f in self.findings if f.severity is Severity.WARNING)

    @classmethod
    def merge(cls, name: str, reports: Iterable[ValidationReport]) -> ValidationReport:
        """Combine several reports into one aggregate under ``name``."""
        findings: list[ValidationFinding] = []
        for report in reports:
            findings.extend(report.findings)
        return cls(name=name, findings=tuple(findings))


def finding(check: str, severity: Severity, message: str) -> ValidationFinding:
    """Construct a :class:`ValidationFinding` (concise helper)."""
    return ValidationFinding(check=check, severity=severity, message=message)


def error(check: str, message: str) -> ValidationFinding:
    """Construct an error-severity finding."""
    return finding(check, Severity.ERROR, message)


def warning(check: str, message: str) -> ValidationFinding:
    """Construct a warning-severity finding."""
    return finding(check, Severity.WARNING, message)


def info(check: str, message: str) -> ValidationFinding:
    """Construct an info-severity finding."""
    return finding(check, Severity.INFO, message)
