"""Fluent dialog builder — construct a :class:`FormSpec` via chained method calls.

Example::

    spec = (
        DialogBuilder("My Form")
        .min_size(600, 400)
        .add_label("Section Header", row=0, col=0, font=TkFont("Arial", 12, "bold", "roman", False, False).value)
        .add_text("username", label="Username", default="user", row=1, col=0)
        .add_select("visibility", label="Visibility", default="local",
                     options=["public", "private", "local"], row=2, col=0)
        .add_checkbox("notify", label="Send notification", default=True, row=3, col=0)
        .add_button("Submit", row=4, col=0)
        .add_button("Cancel", row=4, col=1)
        .build()
    )
"""

from __future__ import annotations

from collections.abc import Callable

from .result import FormResult
from .spec import FieldKind, FieldSpec, FormSpec, TkFont, TkFontDescription, ValidatorFn


class DialogBuilder:
    """Fluent builder that produces a :class:`FormSpec`."""

    def __init__(self, title: str, debug: bool = False) -> None:
        self._title = title
        self._fields: list[FieldSpec] = []
        self._min_width: int = 520
        self._min_height: int = 320
        self._debug = debug

    # -- sizing ------------------------------------------------------------

    def min_size(self, width: int, height: int) -> DialogBuilder:
        """Set the dialog minimum size in pixels."""
        self._min_width = width
        self._min_height = height
        return self

    # -- field helpers -----------------------------------------------------

    def add_label(
        self,
        text: str,
        *,
        row: int = 0,
        col: int = 0,
        font: TkFontDescription | None = None,
        is_bound: bool = False,
    ) -> DialogBuilder:
        """Add a decorative label (no key / no result)."""
        tk_font = font or TkFont().value

        self._fields.append(
            FieldSpec(
                kind=FieldKind.LABEL,
                label=text,
                row=row,
                col=col,
                font=tk_font,
                is_bound=is_bound,
            )
        )
        return self

    def add_text(
        self,
        key: str,
        *,
        label: str = "",
        default: str = "",
        help_text: str = "",
        callback: Callable[..., str] | None = None,
        row: int = 0,
        col: int = 0,
        validators: list[ValidatorFn] | None = None,
        font: TkFontDescription | None = None,
        is_bound: bool = False,
    ) -> DialogBuilder:
        """Add a text entry field."""
        self._fields.append(
            FieldSpec(
                kind=FieldKind.TEXT,
                key=key,
                label=label,
                default=default,
                help_text=help_text,
                callback=callback,
                row=row,
                col=col,
                validators=validators or [],
                font=font or TkFont().value,
                is_bound=is_bound,
            )
        )
        return self

    def add_select(
        self,
        key: str,
        *,
        label: str = "",
        default: str = "",
        help_text: str = "",
        callback: Callable[..., str] | None = None,
        options: list[str] | None = None,
        readonly: bool = False,
        row: int = 0,
        col: int = 0,
        validators: list[ValidatorFn] | None = None,
        font: TkFontDescription | None = None,
        is_bound: bool = False,
    ) -> DialogBuilder:
        """Add a combobox / select field."""
        self._fields.append(
            FieldSpec(
                kind=FieldKind.SELECT,
                key=key,
                label=label,
                default=default,
                help_text=help_text,
                callback=callback,
                options=options or [],
                readonly=readonly,
                row=row,
                col=col,
                validators=validators or [],
                font=font or TkFont().value,
                is_bound=is_bound,
            )
        )
        return self

    def add_checkbox(
        self,
        key: str,
        *,
        label: str = "",
        default: bool = False,
        help_text: str = "",
        callback: Callable[..., str] | None = None,
        bind_to: str | None = None,
        row: int = 0,
        col: int = 0,
        font: TkFontDescription | None = None,
        is_bound: bool = False,
    ) -> DialogBuilder:
        """Add a checkbox field."""
        self._fields.append(
            FieldSpec(
                kind=FieldKind.CHECKBOX,
                key=key,
                label=label,
                default=default,
                help_text=help_text,
                callback=callback,
                bind_to=bind_to,
                row=row,
                col=col,
                font=font or TkFont().value,
                is_bound=is_bound,
            )
        )
        return self

    def add_button(
        self,
        text: str,
        *,
        help_text: str = "",
        callback: Callable[..., str] | None = None,
        bind_to: str | None = None,
        row: int = 0,
        col: int = 0,
        font: TkFontDescription | None = None,
        is_bound: bool = False,
    ) -> DialogBuilder:
        """Add a button.

        Buttons with ``text`` equal to ``"Submit"`` or ``"Cancel"``
        (case-insensitive) automatically receive submit / cancel behaviour
        when *callback* is ``None``.
        """
        self._fields.append(
            FieldSpec(
                kind=FieldKind.BUTTON,
                key=text.lower(),
                label=text.title(),
                help_text=help_text,
                callback=callback,
                bind_to=bind_to,
                row=row,
                col=col,
                font=font or TkFont().value,
                is_bound=is_bound,
            )
        )
        return self

    # -- build -------------------------------------------------------------

    def build(self) -> FormSpec:
        """Produce the final :class:`FormSpec`."""
        return FormSpec(
            title=self._title,
            fields=self._fields,
            min_width=self._min_width,
            min_height=self._min_height,
        )

    # -- shortcut ----------------------------------------------------------

    def show(self) -> "FormResult":
        """Build *and* immediately show the dialog, returning :class:`FormResult`."""
        from .dialog import FormDialog

        return FormDialog(self.build(), debug=self._debug).show()
