"""Generic form result container, decoupled from any specific config type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FormResult:
    """Result returned by :meth:`FormDialog.show`.

    Attributes:
        cancelled: ``True`` when the user closed/cancelled the dialog.
        values: Raw ``{key: value}`` mapping collected from form fields.
    """

    cancelled: bool = True
    values: dict[str, Any] = field(default_factory=dict)
