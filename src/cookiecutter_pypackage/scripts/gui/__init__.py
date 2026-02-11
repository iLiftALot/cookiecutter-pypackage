"""Reusable Tk/ttk GUI framework for building professional form dialogs.

Public API
----------

Declarative
~~~~~~~~~~~
- :class:`FormSpec` — complete form specification.
- :class:`FieldSpec` — specification for a single field.
- :class:`FieldKind` — field type discriminator.

Builder (fluent)
~~~~~~~~~~~~~~~~
- :class:`DialogBuilder` — chainable builder producing a ``FormSpec``.

Renderer
~~~~~~~~
- :class:`FormDialog` — renders a ``FormSpec`` as a modal dialog.

Result
~~~~~~
- :class:`FormResult` — generic result container.

Validation
~~~~~~~~~~
- :class:`ValidationResult`, :class:`ValidationIssue`, :class:`Severity`
- :func:`required`, :func:`choices`, :func:`path_exists`, :func:`no_spaces_warning`

Tooltip
~~~~~~~
- :class:`CreateToolTip` — legacy tooltip utility (unchanged).

Window utilities
~~~~~~~~~~~~~~~~
- :func:`center_window`, :func:`bring_to_front_briefly`, :func:`make_modal`,
  :func:`ask_directory`
"""

from .builder import DialogBuilder
from .dialog import FormDialog
from .result import FormResult
from .spec import FieldKind, FieldSpec, FormSpec
from .tooltip import CreateToolTip
from .validation import (
    Severity,
    ValidationIssue,
    ValidationResult,
    choices,
    no_spaces_warning,
    path_exists,
    required,
)
from .window import ask_directory, bring_to_front_briefly, center_window, make_modal

__all__ = [
    # Spec
    "FormSpec",
    "FieldSpec",
    "FieldKind",
    # Builder
    "DialogBuilder",
    # Renderer
    "FormDialog",
    # Result
    "FormResult",
    # Validation
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    "required",
    "choices",
    "path_exists",
    "no_spaces_warning",
    # Tooltip
    "CreateToolTip",
    # Window
    "center_window",
    "bring_to_front_briefly",
    "make_modal",
    "ask_directory",
]
