"""Declarative form specification — ``FormSpec`` and ``FieldSpec`` variants.

Build a ``FormSpec`` either directly (declarative) or via
:class:`~cookiecutter_pypackage.scripts.gui.builder.DialogBuilder` (fluent).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from .font import TkFont, TkFontDescription
from .validation import ValidationReport
from enum import StrEnum, auto
from typing import Any

# ---------------------------------------------------------------------------
# Field kinds
# ---------------------------------------------------------------------------


class FieldKind(StrEnum):
    """Discriminator for :class:`FieldSpec`."""

    TEXT = auto()
    SELECT = auto()
    CHECKBOX = auto()
    BUTTON = auto()
    LABEL = auto()


# ---------------------------------------------------------------------------
# Validator reference (for spec-level declaration)
# ---------------------------------------------------------------------------

type ValidatorFn = Callable[[Any], ValidationReport]
"""A callable that receives the current field value and returns an error
message string if invalid, or ``None`` if valid."""


# ---------------------------------------------------------------------------
# FieldSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """Specification for a single form field.

    Parameters:
        kind: The type of widget to render.
        key: Unique identifier used as the result-dict key.  ``None`` for
            decorative fields (labels, standalone buttons).
        label: Display text shown next to the widget.
        default: Default value (type depends on *kind*).
        help_text: Tooltip text shown on hover.
        options: For ``SELECT`` fields — the list of valid choices.
        readonly: For ``SELECT`` fields — whether the combobox is read-only.
        callback: For ``BUTTON`` fields — the function to invoke on click.
            Return value (if ``str``) is pushed into the *bind_to* field.
        bind_to: For ``BUTTON`` fields — the *key* of the target field whose
            value should be updated with the callback's return value.
        row: Grid row index (0-based).
        col: Grid column index (0-based).
        validators: Optional list of :data:`ValidatorFn` callables.
        font: Optional ``(family, size, weight, slant, underline, overstrike)`` tuple for ``LABEL`` fields.
    """

    kind: FieldKind
    key: str | None = None
    label: str = ""
    default: Any = None
    help_text: str = ""
    options: list[str] = field(default_factory=list)
    readonly: bool = False
    callback: Callable[..., str | None] | None = None
    bind_to: str | None = None
    row: int = 0
    col: int = 0
    validators: list[ValidatorFn] = field(default_factory=list)
    font: TkFontDescription = field(default_factory=lambda: TkFont().value)
    is_bound: bool = field(default=False)


# ---------------------------------------------------------------------------
# FormSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FormSpec:
    """Complete specification for a form dialog.

    Parameters:
        title: Window title.
        fields: Ordered list of :class:`FieldSpec` instances.
        min_width: Minimum dialog width in pixels.
        min_height: Minimum dialog height in pixels.
    """

    title: str
    fields: list[FieldSpec] = field(default_factory=list)
    min_width: int = 520
    min_height: int = 320
