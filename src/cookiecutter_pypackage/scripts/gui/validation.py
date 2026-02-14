"""Reusable field validators and validation result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from typing import Any, Callable, NamedTuple

# ---------------------------------------------------------------------------
# Validation Levels and Result Types
# ---------------------------------------------------------------------------


class Severity(StrEnum):
    """How serious a validation finding is."""

    ERROR = auto()
    WARNING = auto()
    OK = auto()


class ValidationStatus(StrEnum):
    """Overall validation status for a form submission."""

    VALID = auto()
    INVALID = auto()


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single validation finding attached to a field."""

    severity: Severity
    field_key: str
    message: str


class ValidationReport(NamedTuple):
    """Collects validation issues for a single field."""

    status: ValidationStatus
    severity: Severity
    message: str | None
    value: Any | None


# ---------------------------------------------------------------------------
# Aggregate result
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Collects :class:`ValidationIssue` instances for a form submission."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == Severity.WARNING for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def error_messages_for(self, key: str) -> list[str]:
        return [
            i.message
            for i in self.issues
            if i.field_key == key and i.severity == Severity.ERROR
        ]

    def warning_messages_for(self, key: str) -> list[str]:
        return [
            i.message
            for i in self.issues
            if i.field_key == key and i.severity == Severity.WARNING
        ]


# ---------------------------------------------------------------------------
# Common validators
# ---------------------------------------------------------------------------


def required(value: Any) -> ValidationReport:
    """Value must be non-empty / non-None."""
    if value is None:
        return ValidationReport(
            ValidationStatus.INVALID, Severity.ERROR, "This field is required.", value
        )
    if isinstance(value, str) and not value.strip():
        return ValidationReport(
            ValidationStatus.INVALID, Severity.ERROR, "This field is required.", value
        )
    return ValidationReport(ValidationStatus.VALID, Severity.OK, None, value)


def choices(*valid_choices: str) -> Callable[[Any], ValidationReport]:
    """Value must be one of *valid_choices*."""

    def _validate(value: Any) -> ValidationReport:
        if value not in valid_choices:
            return ValidationReport(
                ValidationStatus.INVALID,
                Severity.ERROR,
                f"Must be one of: {', '.join(valid_choices)}",
                value,
            )
        return ValidationReport(ValidationStatus.VALID, Severity.OK, None, value)

    return _validate


def path_exists(value: str) -> ValidationReport:
    """Value must be an existing filesystem path."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return ValidationReport(
            ValidationStatus.INVALID, Severity.ERROR, "Path is required.", value
        )

    p = Path(value).expanduser()

    # Absolute paths — check directly.
    if p.is_absolute():
        if not p.exists():
            return ValidationReport(
                ValidationStatus.INVALID,
                Severity.ERROR,
                f"Path does not exist: {p}",
                value,
            )
        return ValidationReport(ValidationStatus.VALID, Severity.OK, None, value)

    # Relative paths — walk up from CWD to find the correct base.
    base = Path.cwd()
    while True:
        candidate = base / p
        if candidate.exists():
            break
        parent = base.parent
        if parent == base:
            break
        base = parent
    
    if not candidate.exists():
        return ValidationReport(
            ValidationStatus.INVALID, Severity.ERROR, f"Path does not exist: {p}", value
        )
    return ValidationReport(ValidationStatus.VALID, Severity.OK, None, value)


def no_spaces_warning(value: Any) -> ValidationReport:
    """Warn (not block) if value contains spaces."""
    if isinstance(value, str) and " " in value.strip():
        return ValidationReport(
            ValidationStatus.INVALID,
            Severity.WARNING,
            "Contains spaces — this may cause issues.",
            value,
        )
    return ValidationReport(ValidationStatus.VALID, Severity.OK, None, value)
