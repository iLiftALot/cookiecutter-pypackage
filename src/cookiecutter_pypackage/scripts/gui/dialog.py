"""FormDialog — renders a :class:`FormSpec` as a professional modal Tk dialog.

Usage::

    from cookiecutter_pypackage.scripts.gui.dialog import FormDialog
    from cookiecutter_pypackage.scripts.gui.spec import FormSpec, FieldSpec, FieldKind

    spec = FormSpec(title="Example", fields=[...])
    result = FormDialog(spec).show()
    if not result.cancelled:
        print(result.values)
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    NamedTuple,
    Protocol,
    TypeGuard,
    overload,
)

import customtkinter as ctk

from ...run import console
from .result import FormResult
from .spec import FieldKind, FieldSpec, FormSpec, TkFont
from .tooltip import CreateToolTip
from .validation import ValidationIssue, ValidationResult, ValidationStatus
from .window import bring_to_front_briefly, center_window

if TYPE_CHECKING:
    from tkinter import _GridInfo, _PackInfo

# ---------------------------------------------------------------------------
# Widget type alias
# ---------------------------------------------------------------------------


type _TraceMode = Literal["array", "read", "write", "unset"]


class CTkSeparator(ctk.CTkFrame):
    """CTk doesn't have a built-in separator widget, so we use a thin frame instead."""

    def __init__(
        self,
        master: ctk.CTk | ctk.CTkToplevel,
        width: int = 1,
        height: int = 1,
        fg_color: str = "gray50",
        border_color: str = "gray50",
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            fg_color=fg_color,
            border_color=border_color,
        )


class Gridded(Protocol):
    def grid_info(self) -> _GridInfo: ...


class Packed(Protocol):
    def pack_info(self) -> _PackInfo: ...


type CTkWidget = (
    ctk.CTkFrame
    | ctk.CTkButton
    | ctk.CTkCheckBox
    | ctk.CTkEntry
    | ctk.CTkComboBox
    | ctk.CTkLabel
    | ctk.CTkOptionMenu
    | ctk.CTkProgressBar
    | ctk.CTkRadioButton
    | ctk.CTkScrollableFrame
    | tk.Misc
    | tk.Widget
    | ctk.CTkBaseClass
    | CTkSeparator
    | ctk.CTkScrollbar
    | ctk.CTkSegmentedButton
    | ctk.CTkSlider
    | ctk.CTkTabview
    | ctk.CTkSwitch
    | ctk.CTkTextbox
)

CTkWidgetClass = (
    tk.Misc,
    tk.Widget,
    ctk.CTkBaseClass,
    ctk.CTkFrame,
    ctk.CTkButton,
    ctk.CTkCheckBox,
    ctk.CTkEntry,
    ctk.CTkComboBox,
    ctk.CTkLabel,
    ctk.CTkOptionMenu,
    ctk.CTkProgressBar,
    ctk.CTkRadioButton,
    ctk.CTkScrollableFrame,
    ctk.CTkScrollbar,
    ctk.CTkSegmentedButton,
    ctk.CTkSlider,
    ctk.CTkTabview,
    ctk.CTkSwitch,
    ctk.CTkTextbox,
    CTkSeparator,
)


class CTkEvent[T: (tk.Misc, ctk.CTkBaseClass)](Protocol):
    """Container for the properties dof an event.

    Instances of this type are generated if one of the following events occurs:
        - `KeyPress, KeyRelease` - **for keyboard events**
        - `ButtonPress, ButtonRelease, Motion, Enter, Leave, MouseWheel` - **for mouse events**
        - `Visibility, Unmap, Map, Expose, FocusIn, FocusOut, Circulate, Colormap, Gravity`
        `Reparent, Property, Destroy, Activate, Deactivate` - **for window events.**

    If a callback function for one of these events is registered
    using bind, bind_all, bind_class, or tag_bind, the callback is
    called with an Event as first argument. It will have the
    following attributes (in braces are the event types for which
    the attribute is valid):

        - `serial` - serial number of event
        - `num` - mouse button pressed (ButtonPress, ButtonRelease)
        - `focus` - whether the window has the focus (Enter, Leave)
        - `height` - height of the exposed window (Configure, Expose)
        - `width` - width of the exposed window (Configure, Expose)
        - `keycode` - keycode of the pressed key (KeyPress, KeyRelease)
        - `state` - state of the event as a number (ButtonPress, ButtonRelease,
                                Enter, KeyPress, KeyRelease,
                                Leave, Motion)
        - `state` - state as a string (Visibility)
        - `time` - when the event occurred
        - `x` - x-position of the mouse
        - `y` - y-position of the mouse
        - `x_root` - x-position of the mouse on the screen
                (ButtonPress, ButtonRelease, KeyPress, KeyRelease, Motion)
        - `y_root` - y-position of the mouse on the screen
                (ButtonPress, ButtonRelease, KeyPress, KeyRelease, Motion)
        - `char` - pressed character (KeyPress, KeyRelease)
        - `send_event` - see X/Windows documentation
        - `keysym` - keysym of the event as a string (KeyPress, KeyRelease)
        - `keysym_num` - keysym of the event as a number (KeyPress, KeyRelease)
        - `type` - type of the event as a number
        - `widget` - widget in which the event occurred
        - `delta` - delta of wheel movement (MouseWheel)
    """

    serial: int
    num: int
    focus: bool
    height: int
    width: int
    keycode: int
    state: int | str
    time: int
    x: int
    y: int
    x_root: int
    y_root: int
    char: str
    send_event: bool
    keysym: str
    keysym_num: int
    type: tk.EventType
    widget: T
    delta: int

    def __repr__(self) -> str: ...


_CTkEvent = CTkEvent[CTkWidget]


class GridInfo(NamedTuple):
    column: int
    columnspan: int
    padx: tuple[int, int]
    pady: tuple[int, int]
    grid_row: int


# ---------------------------------------------------------------------------
# FormDialog
# ---------------------------------------------------------------------------


class FormDialog:
    """Renders a :class:`FormSpec` as a modal ``Toplevel`` dialog.

    Call :meth:`show` to display the dialog and block until the user submits
    or cancels.  Returns a :class:`FormResult`.
    """

    type BIND_COMMAND = Literal[
        "select_all",
        "focus",
        # "bring_to_front",
        # "center_window",
        "undo",
        "redo",
        "copy",
        "paste",
        "cut",
    ]
    type BIND_MODIFIER = Literal[
        "<Command-a>",
        "<Command-c>",
        "<Command-v>",
        "<Command-x>",
        "<Command-z>",
        "<Command-Shift-z>",
        "<Button-1>",
        "<Button-2>",
        "<Button-3>",
    ]
    type BIND_SEQUENCE = Literal[
        "<<Undo>>", "<<Redo>>", "<<Copy>>", "<<Paste>>", "<<Cut>>"
    ]

    BIND_CALLBACK_MAP: ClassVar[dict[BIND_COMMAND, Callable[[_CTkEvent], None]]] = {
        "select_all": lambda e: (
            e.widget.select_range(0, ctk.END)
            if isinstance(e.widget, ctk.CTkEntry)
            else None
        ),
        "focus": lambda e: (
            e.widget.focus_set() if issubclass(e.widget.__class__, tk.Misc) else None
        ),
        # "bring_to_front": lambda e: bring_to_front_briefly(e.widget.winfo_toplevel()),
        # "center_window": lambda e: center_window(e.widget.winfo_toplevel()),
        "undo": lambda e: e.widget.event_generate("<<Undo>>"),
        "redo": lambda e: e.widget.event_generate("<<Redo>>"),
        "copy": lambda e: e.widget.event_generate("<<Copy>>"),
        "paste": lambda e: e.widget.event_generate("<<Paste>>"),
        "cut": lambda e: e.widget.event_generate("<<Cut>>"),
    }

    BIND_SEQUENCE_MAP: ClassVar[
        dict[BIND_COMMAND, tuple[BIND_MODIFIER, BIND_SEQUENCE | None]]
    ] = {
        "select_all": ("<Command-a>", None),
        "focus": ("<Button-1>", None),
        # "bring_to_front": (),
        # "center_window": ("<FocusIn>", None),
        "undo": ("<Command-z>", "<<Undo>>"),
        "redo": ("<Command-Shift-z>", "<<Redo>>"),
        "copy": ("<Command-c>", "<<Copy>>"),
        "paste": ("<Command-v>", "<<Paste>>"),
        "cut": ("<Command-x>", "<<Cut>>"),
    }

    def __init__(
        self, spec: FormSpec, debug: bool = False, reload: bool = False
    ) -> None:
        self._spec = spec
        self._result = FormResult()
        self._debug = debug
        self._reload = reload

        # Internal state — populated during ``show()``
        self._root: ctk.CTk | None = None
        self._dialog: ctk.CTkToplevel | ctk.Tk | None = None
        self._content: ctk.CTkFrame | None = None
        self._field_vars: dict[str, ctk.Variable] = {}
        self._field_widgets: dict[str, CTkWidget] = {}
        self._field_rows: dict[str, int] = {}
        self._button_widgets: dict[str, ctk.CTkButton] = {}
        self._error_labels: dict[str, ctk.CTkLabel] = {}
        self._first_focus: CTkWidget | None = None
        self._traces: list[tuple[ctk.Variable, _TraceMode, str]] = []

    # -- public API --------------------------------------------------------

    def show(self) -> FormResult:
        """Display the dialog modally and return the collected result."""

        # Use CTk() directly as the dialog window — on macOS, a Toplevel
        # transient to a withdrawn root renders blank.
        self._root = ctk.CTk()
        self._root.title(self._spec.title)
        self._root.minsize(self._spec.min_width, self._spec.min_height)
        self._root.resizable(False, False)
        self._root.config(pady=5, padx=5)
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        # disable full screen on macOS (buggy with modals)
        # self._root.attributes("-fullscreen", False)

        # Cancel semantics
        self._root.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._root.bind("<Escape>", lambda _e: self._on_cancel())
        # Submit on Enter
        self._root.bind("<Return>", lambda _e: self._on_submit())
        # Clicking anywhere focuses the clicked widget (for better keyboard navigation)
        focus_modifier, focus_cb, _ = self.get_bind_info("focus")
        self._root.bind_all(
            focus_modifier,
            focus_cb,
            add="+",
        )

        # _dialog points to the same window for rendering convenience
        self._dialog = self._root
        self._build_content()

        # Position & focus
        center_window(self._root)
        if self._first_focus is not None:
            self._first_focus.focus_set()
        bring_to_front_briefly(self._root)

        # Modal — grab input so the user must interact with this window
        self._root.grab_set()
        self._root.mainloop()

        # Defensive: ensure no Tk objects survive for GC on another thread
        self._field_vars.clear()
        self._field_widgets.clear()
        self._button_widgets.clear()
        self._error_labels.clear()
        self._traces.clear()
        self._first_focus = None
        self._content = None
        self._dialog = None
        self._root = None

        return self._result

    @staticmethod
    def get_bind_info(
        command: BIND_COMMAND, modifier: BIND_MODIFIER | None = None
    ) -> tuple[BIND_MODIFIER, Callable[[_CTkEvent], None], BIND_SEQUENCE | None]:
        """Get the callback function and modifier sequence for a given bind command."""
        if command not in FormDialog.BIND_CALLBACK_MAP:
            raise ValueError(f"Unsupported bind command: {command}")

        cls = FormDialog
        callback = cls.BIND_CALLBACK_MAP[command]
        default_modifier, sequence = cls.BIND_SEQUENCE_MAP[command]
        return (modifier or default_modifier, callback, sequence)

    # -- layout ------------------------------------------------------------

    def _build_content(self) -> None:
        """Build a flat grid so label / entry / button columns align across
        all rows.  Action buttons (Submit, Cancel, …) are collected into a
        compact right-aligned bar separated from the form fields.
        """
        assert self._dialog is not None

        # ── outer content frame ──────────────────────────────────────────
        self._content = ctk.CTkFrame(self._dialog)
        self._content.grid(row=0, column=0, sticky="nsew")
        #   col 0 = labels   (fixed)
        #   col 1 = entries   (stretches)
        #   col 2 = aux buttons like "Browse…"  (fixed)
        #   col 3 = action buttons like "Submit" (in the button bar, handled separately)
        self._content.columnconfigure(0, weight=0) # other values for uniform:
        self._content.columnconfigure(1, weight=1, uniform="cols")
        self._content.columnconfigure(2, weight=0, uniform="cols")
        self._content.columnconfigure(3, weight=0)
        # self._content.columnconfigure(4, weight=0)

        # ── partition fields ─────────────────────────────────────────────
        form_fields: list[FieldSpec] = []
        action_buttons: list[FieldSpec] = []

        if self._reload and not self._debug:
            self._debug = True

        # Filter out stale debug FieldSpecs injected by a previous reload
        self._spec.fields[:] = [
            f for f in self._spec.fields if not f.label.startswith("DEBUG:")
        ]

        for f in self._spec.fields:
            if f.kind == FieldKind.BUTTON and not f.bind_to:
                action_buttons.append(f)
            else:
                form_fields.append(f)

        # ── render form fields into the flat grid ────────────────────────
        # Use spec.row * 2 as the grid row so there is always a free row
        # (spec.row * 2 + 1) available for inline validation errors.
        for field_spec in sorted(form_fields, key=lambda f: (f.row, f.col)):
            self._render_field(field_spec)

        # ── separator + action-button bar ────────────────────────────────
        btn_row = 0
        if action_buttons:
            # sep_row = (max(f.row for f in self._spec.fields) + 1) * 2
            sep_row = self._get_lowest_available_row()
            sep = CTkSeparator(self._content)
            sep.grid(
                row=sep_row,
                column=0,
                columnspan=3,
                sticky=ctk.EW,
                pady=(15, 15),
            )

            btn_row = sep_row + 1
            btn_frame = ctk.CTkFrame(self._content)
            btn_frame.grid(
                row=btn_row,
                column=0,
                columnspan=3,
                sticky=ctk.EW,
                pady=(0, 0),
            )
            btn_frame.columnconfigure(0, weight=1)
            btn_frame.columnconfigure(3, weight=1)

            for idx, btn_spec in enumerate(action_buttons, 1):
                cb = self._resolve_button_callback(btn_spec)
                btn = ctk.CTkButton(btn_frame, text=btn_spec.label, command=cb)
                padx = (2, 2)
                if idx == 1:
                    padx = (20, 2)
                elif idx == len(action_buttons):
                    padx = (2, 20)
                btn.pack(side="left", fill="x", padx=padx, expand=True)
                # Track for debug output
                btn_key = btn_spec.label.lower().replace(" ", "_").replace(":", "")
                self._button_widgets[btn_key] = btn

        # ── debug buttons (below the action bar) ─────────────────────────
        if self._debug:
            self._add_debug_buttons(btn_row)

        # ── attach tooltips to all widgets in one pass ───────────
        self._attach_tooltips()

    # -- field rendering ---------------------------------------------------

    def _render_field(self, spec: FieldSpec) -> None:
        """Render a single :class:`FieldSpec` into *parent*."""
        renderer = _RENDERERS.get(spec.kind)
        if renderer is None:
            raise ValueError(f"Unsupported field kind: {spec.kind}")

        col, colspan, padx, pady, grid_row = 1, 1, (1, 1), (2, 2), spec.row * 2
        if spec.kind in (FieldKind.TEXT, FieldKind.SELECT):
            if not spec.label and not spec.is_bound:
                # Standalone text field without a label or button
                # - stretch across entire width.
                col, colspan, padx, pady = 0, 3, (7, 7), (2, 2)
            elif not spec.label and spec.is_bound:
                # No label but bound to a button (e.g. Browse…)
                # — leave space for the button on the right
                col, colspan, padx, pady = 0, 2, (1, 1), (2, 2)
            elif spec.label and not spec.is_bound:
                # Label on the left but no button on the right
                # — stretch to the right edge
                col, colspan, padx, pady = 1, 2, (1, 7), (2, 2)
            else:  # spec.label and spec.is_bound
                # Label on the left and button on the right
                # — entry in the middle, stretching to fill space between
                col, colspan, padx, pady = 1, 1, (1, 1), (2, 2)
        elif spec.kind == FieldKind.LABEL:
            # Labels always stretch full width
            # — they are section headers, not field labels.
            col, colspan, padx, pady = 0, 3, (7, 7), (8, 4)
        elif spec.kind == FieldKind.CHECKBOX:
            if spec.is_bound:
                padx = (1, 1) if spec.label else (7, 1)
            else:
                padx = (1, 7) if spec.label else (7, 7)
            # Checkboxes always sit in the label column on the left
            col, colspan = (1, 2) if spec.label else (0, 2)
        else:
            # BUTTON fields
            if spec.bind_to:
                col, colspan = 2, 1
                padx = (1, 7) if spec.label else (7, 7)
                # Resolve the grid row of the field this button is bound to
                grid_row = self._field_rows.get(spec.bind_to, grid_row)
            else:
                col, colspan, padx = 1, 2, (1, 7)

        renderer(self, spec, GridInfo(col, colspan, padx, pady, grid_row))

    def _render_label(self, spec: FieldSpec, grid_info: GridInfo) -> None:
        font = spec.font if spec.font else TkFont().value
        lbl = ctk.CTkLabel(self._content, text=spec.label, font=font)
        lbl.grid(
            row=grid_info.grid_row,
            column=grid_info.column,
            columnspan=grid_info.columnspan,
            padx=grid_info.padx,
            pady=grid_info.pady,
            sticky=ctk.W,
            # Position text in the middle
            anchor=ctk.CENTER,
        )

    def _render_text(
        self,
        spec: FieldSpec,
        grid_info: GridInfo,
    ) -> None:
        if spec.label:
            lbl = ctk.CTkLabel(self._content, text=spec.label)
            lbl.grid(
                row=grid_info.grid_row, column=0, sticky=ctk.W, padx=(7, 1), pady=2
            )

        var = ctk.StringVar(master=self._root, value=spec.default or "")
        entry = ctk.CTkEntry(self._content, textvariable=var)
        entry.grid(
            row=grid_info.grid_row,
            column=grid_info.column,
            columnspan=grid_info.columnspan,
            padx=grid_info.padx,
            pady=grid_info.pady,
            sticky=ctk.EW,
        )
        # Select all text on focus
        # entry.bind("<Button-3>", lambda e: e.widget.select_range(0, ctk.END))
        select_all_modifier, select_all_cb, _ = self.get_bind_info("select_all")
        entry.bind(select_all_modifier, select_all_cb, add="+")

        if spec.key:
            self._field_vars[spec.key] = var
            self._field_widgets[spec.key] = entry
            self._field_rows[spec.key] = grid_info.grid_row
        if self._first_focus is None:
            self._first_focus = entry

    def _render_select(self, spec: FieldSpec, grid_info: GridInfo) -> None:
        if spec.label:
            lbl = ctk.CTkLabel(self._content, text=spec.label)
            lbl.grid(
                row=grid_info.grid_row, column=0, sticky=ctk.W, padx=(7, 1), pady=2
            )

        var = ctk.StringVar(master=self._root, value=spec.default or "")
        state = "readonly" if spec.readonly else "normal"
        combo = ctk.CTkComboBox(
            self._content,
            values=spec.options,
            variable=var,
            state=state,
        )
        combo.grid(
            row=grid_info.grid_row,
            column=grid_info.column,
            columnspan=grid_info.columnspan,
            padx=grid_info.padx,
            pady=grid_info.pady,
            sticky=ctk.EW,
        )

        if spec.key:
            self._field_vars[spec.key] = var
            self._field_widgets[spec.key] = combo
            self._field_rows[spec.key] = grid_info.grid_row
        if self._first_focus is None:
            self._first_focus = combo

    def _render_checkbox(self, spec: FieldSpec, grid_info: GridInfo) -> None:
        if spec.label:
            lbl = ctk.CTkLabel(self._content, text=spec.label)
            lbl.grid(
                row=grid_info.grid_row, column=0, sticky=ctk.W, padx=(7, 1), pady=2
            )

        var = ctk.BooleanVar(master=self._root, value=bool(spec.default))
        chk = ctk.CTkCheckBox(self._content, text=spec.label, variable=var)
        chk.grid(
            row=grid_info.grid_row,
            column=grid_info.column,
            columnspan=grid_info.columnspan,
            padx=grid_info.padx,
            pady=grid_info.pady,
            sticky=ctk.W,
        )

        if spec.key:
            self._field_vars[spec.key] = var
            self._field_widgets[spec.key] = chk

    def _render_button(self, spec: FieldSpec, grid_info: GridInfo) -> None:
        """Render an *auxiliary* button (e.g. Browse…) bound to a field.

        Standalone action buttons (Submit / Cancel) are handled directly
        by :meth:`_build_content` and never reach this renderer.
        """
        if not (target_key := spec.bind_to):
            return  # safety — should not happen

        callback = self._resolve_button_callback(spec)
        if callable(spec.callback):
            original_cb = spec.callback

            def action() -> None:
                result = original_cb()
                if result is None or target_key is None:
                    return
                target_var = self._field_vars.get(target_key)
                if target_var is not None:
                    target_var.set(result)

            callback = action

        btn = ctk.CTkButton(self._content, text=spec.label, command=callback)
        btn.grid(
            row=grid_info.grid_row,
            column=grid_info.column,
            columnspan=grid_info.columnspan,
            padx=grid_info.padx,
            pady=grid_info.pady,
            sticky=ctk.EW,
        )
        # Track for debug output
        btn_key = spec.label.lower().replace(" ", "_").replace(":", "")
        self._button_widgets[btn_key] = btn

    # -- callbacks ---------------------------------------------------------

    def _resolve_button_callback(self, spec: FieldSpec) -> Callable[[], None]:
        """Determine the actual callback for a button spec."""
        if spec.callback is not None:
            cb = spec.callback
            return lambda: cb()  # type: ignore[return-value]

        # Auto-wire Submit / Cancel by label
        label_lower = spec.label.strip().lower()
        if label_lower == "submit":
            return self._on_submit
        if label_lower == "cancel":
            return self._on_cancel
        raise ValueError(
            f"Button '{spec.label}' has no callback and is not 'Submit' or 'Cancel'."
        )

    def _on_submit(self) -> None:
        """Collect values, validate, and close if valid."""
        values = self._collect_var_values()

        # Run validation
        vr = self._validate(values)
        self._clear_errors()

        if vr.has_errors:
            self._display_errors(vr)
            return

        if vr.has_warnings:
            msgs = "\n".join(f"• {w.message}" for w in vr.warnings)
            tkfont = TkFont("TkDefaultFont", weight="bold", slant="italic")
            proceed = ctk.CTkInputDialog(
                title="Warning",
                text=f"The following warnings were found:\n\n{msgs}\n\nProceed anyway?",
                font=ctk.CTkFont(**{**tkfont}),
            ).get_input()
            if not proceed:
                return

        self._result.cancelled = False
        self._result.values = values
        self._close()

    def _on_cancel(self) -> None:
        """Cancel and close the dialog."""
        self._result.cancelled = True
        self._close()

    def _close(self) -> None:
        # Clear all Tk Variable / widget references BEFORE destroying the
        # Tcl interpreter.  If we don't, Python's GC may finalise the
        # StringVar / BooleanVar objects later from the asyncio thread,
        # triggering "main thread is not in main loop" / Tcl_AsyncDelete.
        self._remove_all_traces()
        self._field_vars.clear()
        self._field_widgets.clear()
        self._button_widgets.clear()
        self._error_labels.clear()
        self._first_focus = None
        if self._dialog:
            self._dialog.destroy()
            self._dialog = None
            self._root = None

    # -- value collection --------------------------------------------------

    def _collect_var_values(self) -> dict[str, Any]:
        """Read current values from all keyed field variables."""
        values: dict[str, Any] = {}
        for key, var in self._field_vars.items():
            raw = var.get()
            # Normalise strings
            if isinstance(raw, str):
                raw = raw.strip()
                if not raw:
                    raw = None
            values[key] = raw
        return values

    @overload
    def _trace[T](
        self,
        variable: ctk.Variable,
        mode: _TraceMode,
        *,
        obj: T,
        attr: str,
    ) -> str: ...
    @overload
    def _trace[T](
        self, variable: ctk.Variable, mode: _TraceMode, *, callback: Callable[..., T]
    ) -> str: ...
    def _trace[T](
        self,
        variable: ctk.Variable,
        mode: _TraceMode,
        *,
        obj: Any | None = None,
        attr: str | None = None,
        callback: Callable[..., T] | None = None,
    ) -> str:
        """Register a Tk variable trace and track it for cleanup.

        Either supply *obj* + *attr* (sets ``obj.attr = variable.get()``
        on every trace event) **or** a raw *callback*.

        Returns the trace-id string so the caller can remove it
        individually if needed.
        """
        if callback is not None:
            cb = callback
        elif obj is not None and attr is not None:
            if not hasattr(obj, attr):
                raise AttributeError(f"{obj!r} has no attribute '{attr}'")

            def _(*_args) -> T:
                setattr(obj, attr, variable.get())
                return obj

            cb = _
        else:
            raise ValueError("_trace requires either (obj + attr) or callback.")

        trace_id: str = variable.trace_add(mode, cb)
        self._traces.append((variable, mode, trace_id))
        return trace_id

    def _remove_all_traces(self) -> None:
        """Remove every registered trace — call before destroying Tk."""
        for variable, mode, trace_id in self._traces:
            try:
                variable.trace_remove(mode, trace_id)
            except ctk.TclError:
                pass  # already gone
        self._traces.clear()

    def _get_lowest_available_row(self) -> int:
        """Calculate the lowest available grid row index for debug buttons."""
        return (max(f.row for f in self._spec.fields) + 1) * 2

    def _attach_tooltips(self) -> None:
        """Walk all widgets and attach debug tooltips in one pass.

        CTk widgets are *compound* — a ``CTkEntry`` is a frame containing
        an internal ``tk.Entry``.  We must treat interactive CTk widgets as
        **leaf nodes** (no recursion into children) so that tooltips attach
        to the outer widget and report its real grid/pack position, not the
        internal layout of its sub-widgets.
        """
        # Build a reverse lookup: widget id → FieldSpec
        widget_to_spec: dict[int, FieldSpec] = {}
        for spec in self._spec.fields:
            if spec.key and spec.key in self._field_widgets:
                widget_to_spec[id(self._field_widgets[spec.key])] = spec
            btn_key = spec.label.lower().replace(" ", "_").replace(":", "")
            if btn_key in self._button_widgets:
                widget_to_spec[id(self._button_widgets[btn_key])] = spec

        debug_cb = self._debug_tooltip if self._debug else None

        # CTk compound widgets — attach tooltip but never recurse into
        # their internal children (tk.Entry inside CTkEntry, etc.).
        _LEAF_TYPES = (
            ctk.CTkEntry,
            ctk.CTkButton,
            ctk.CTkLabel,
            ctk.CTkCheckBox,
            ctk.CTkComboBox,
        )

        def _walk(widget: CTkWidget) -> None:
            # Containers — recurse into children, don't attach a tooltip
            if isinstance(widget, (ctk.CTkFrame, CTkSeparator)):
                for child in widget.winfo_children():
                    _walk(child)
                return

            # ── derive help_text ─────────────────────────────────────
            spec = widget_to_spec.get(id(widget))
            if spec and spec.help_text:
                help_text = spec.help_text
            elif spec and spec.key and spec.key in self._field_vars:
                # text / select / checkbox — mirror the original per-renderer
                # behaviour: use the current variable value as the default
                # tooltip (the trace below keeps it in sync).
                help_text = str(self._field_vars[spec.key].get()) or spec.label
            elif spec:
                help_text = spec.label
            else:
                # Untracked widget (e.g. a field label rendered beside an
                # entry).  Use visible text or fall back to the class name.
                try:
                    help_text = widget.cget("text") or type(widget).__name__
                except (tk.TclError, ValueError):
                    help_text = type(widget).__name__

            tooltip = CreateToolTip(widget, help_text, debug_cb=debug_cb)

            # Wire trace so the tooltip stays in sync with field value
            if spec and spec.key and spec.key in self._field_vars:
                self._trace(
                    self._field_vars[spec.key], "write", obj=tooltip, attr="text"
                )

            # Only recurse for unknown widget types — CTk leaf widgets'
            # children are internal implementation details.
            if not isinstance(widget, _LEAF_TYPES):
                for child in widget.winfo_children():
                    _walk(child)

        if self._content:
            _walk(self._content)

    # -- validation --------------------------------------------------------

    def _validate(self, values: dict[str, Any]) -> ValidationResult:
        """Run all per-field validators declared in the spec."""
        vr = ValidationResult()
        for field_spec in self._spec.fields:
            if field_spec.key is None or not field_spec.validators:
                continue
            value = values.get(field_spec.key)
            for validator_fn in field_spec.validators:
                status, severity, msg, value = validator_fn(value)
                if status == ValidationStatus.VALID:
                    continue
                vr.issues.append(
                    ValidationIssue(
                        field_key=field_spec.key,
                        message=msg or "Invalid value.",
                        severity=severity,
                    )
                )
        return vr

    def _display_errors(self, vr: ValidationResult) -> None:
        """Show inline error labels beneath the erroring fields."""
        for issue in vr.errors:
            widget = self._field_widgets.get(issue.field_key)
            if widget is None:
                continue
            if not isinstance(widget, ctk.CTkBaseClass):
                continue
            parent = widget.master
            # In the flat grid, fields sit at grid_row (= spec.row * 2).
            # The slot immediately below (grid_row + 1) is reserved for errors.
            grid_row = widget.grid_info().get("row", 0)
            tkfont = TkFont(weight="bold", size=12, underline=True)
            err_lbl = ctk.CTkLabel(
                parent,
                height=21,
                text=issue.message,
                corner_radius=5,
                fg_color="red",
                font=ctk.CTkFont(
                    tkfont.family,
                    tkfont.size,
                    tkfont.weight,
                    tkfont.slant,
                    tkfont.underline,
                    tkfont.overstrike,
                ),
            )
            err_lbl.grid(
                row=grid_row + 1,
                column=1,
                columnspan=3,
                sticky=ctk.EW,
                padx=(1, 7),
            )
            self._error_labels[issue.field_key] = err_lbl

    def _clear_errors(self) -> None:
        """Remove all currently displayed inline error labels."""
        for lbl in self._error_labels.values():
            lbl.destroy()
        self._error_labels.clear()

    def _is_packed(self, widget: CTkWidget) -> TypeGuard[Packed]:
        """Determine if a widget is packed."""
        if not hasattr(widget, "pack_info"):
            return False
        try:
            widget.pack_info()
            return True
        except tk.TclError:
            return False

    def _is_gridded(self, widget: CTkWidget) -> TypeGuard[Gridded]:
        """Determine if a widget is gridded."""
        if not hasattr(widget, "grid_info"):
            return False
        try:
            grid_info = widget.grid_info()
            return grid_info
        except tk.TclError:
            return False

    # -- debug ------------------------------------------------------------

    def _debug_tooltip(self, widget: CTkWidget, help_text: str) -> str:
        """Generate a debug tooltip string for a widget."""
        gi: _GridInfo
        pi: _PackInfo

        if self._is_gridded(widget):
            gi = widget.grid_info()
            mapped_grid = {k: gi.get(k) for k in gi.keys()}
            grid_info_str = "\n".join(f"- {k}: {v}" for k, v in mapped_grid.items())
            return f"{help_text}\n\n{'-' * 20}\n\nGRID INFO\n{grid_info_str}\n"
        elif self._is_packed(widget):
            pi = widget.pack_info()
            mapped_pack = {k: pi.get(k) for k in pi.keys()}
            pack_info_str = "\n".join(f"- {k}: {v}" for k, v in mapped_pack.items())
            return f"{help_text}\n\n{'-' * 20}\n\nPACK INFO\n{pack_info_str}\n"
        else:
            return f"{help_text}\n\n{'-' * 20}\n\nNO GRID OR PACK INFO\n(widget is not gridded or packed)\n"

    def _debug_widget_data(self, widget: CTkWidget | None = None) -> None:
        """Print layout info for every widget in the window."""

        def _walk(widget: CTkWidget, depth=0):
            gi: _GridInfo | None = None
            pi: _PackInfo | None = None
            indent = "  " * depth
            name = type(widget).__name__
            if self._is_gridded(widget):
                gi = widget.grid_info()
                info = ", ".join(f"{k}={v}" for k, v in gi.items())
                console.print(f"{indent}{name} [grid] {info}")
                return
            elif self._is_packed(widget):
                pi = widget.pack_info()
                info = ", ".join(f"{k}={v}" for k, v in pi.items())
                console.print(f"{indent}{name} [pack] {info}")
                return

            console.print(f"{indent}{name} (no layout manager)")

        def _recurse(widget: CTkWidget, depth=0):
            _walk(widget, depth)
            for child in widget.winfo_children():
                _recurse(child, depth + 1)

        _recurse(widget or self._root)

    def _debug_print(self) -> None:
        """Print a rich-formatted table of all field state to the console."""
        from rich.panel import Panel
        from rich.table import Table

        assert self._root is not None

        # ── Field values table ───────────────────────────────────────────
        tbl = Table(
            title="Form Field State",
            title_style="bold cyan",
            show_lines=True,
            expand=False,
        )
        tbl.add_column("Key", style="bold yellow", no_wrap=True)
        tbl.add_column("Kind", style="dim")
        tbl.add_column("Label")
        tbl.add_column("Value", style="green", no_wrap=True)
        tbl.add_column("Default", style="dim", overflow="fold")
        tbl.add_column("Row", justify="center")
        tbl.add_column("Col", justify="center")
        tbl.add_column("Widget", style="dim cyan", no_wrap=True)
        tbl.add_column("Grid Info", style="dim")

        values = self._collect_var_values()

        for spec in sorted(self._spec.fields, key=lambda f: (f.row, f.col)):
            key = spec.key or spec.label or "—"
            value = str(values.get(spec.key, "—")) if spec.key else "—"
            # Look up keyed field widgets first, then button widgets by label
            widget: CTkWidget | None = None
            if spec.key:
                widget = self._field_widgets.get(spec.key)
            if widget is None and spec.kind == FieldKind.BUTTON:
                btn_key = spec.label.lower().replace(" ", "_").replace(":", "")
                widget = self._button_widgets.get(btn_key)
            widget_class = type(widget).__name__ if widget else "—"
            widget_info = ""
            if self._is_gridded(widget):
                gi = widget.grid_info()
                widget_info = (
                    f"column={gi.get('column')}, "
                    f"columnspan={gi.get('columnspan')}, "
                    f"row={gi.get('row')}, "
                    f"padx={gi.get('padx')}, "
                    f"pady={gi.get('pady')}, "
                    f"sticky={gi.get('sticky')}, "
                    f"in={gi.get('in')}"
                )
            elif self._is_packed(widget):
                pi = widget.pack_info()
                widget_info = (
                    f"side={pi.get('side')}, "
                    f"padx={pi.get('padx')}, "
                    f"pady={pi.get('pady')}, "
                    f"expand={pi.get('expand')}, "
                    f"fill={pi.get('fill')}, "
                    f"anchor={pi.get('anchor')}, "
                    f"in={pi.get('in')}"
                )
            else:
                widget_info = "no grid or pack info"

            tbl.add_row(
                key,
                spec.kind.value,
                spec.label,
                value,
                str(spec.default) if spec.default is not None else "—",
                str(spec.row),
                str(spec.col),
                widget_class,
                widget_info,
            )

        console.print()
        console.print(tbl)

        # ── Tk variable internals ────────────────────────────────────────
        var_tbl = Table(
            title="Tk Variables",
            title_style="bold magenta",
            show_lines=True,
            expand=False,
        )
        var_tbl.add_column("Key", style="bold yellow", no_wrap=True)
        var_tbl.add_column("Type", style="dim")
        var_tbl.add_column("Raw .get()", style="green")
        var_tbl.add_column("Trace IDs", style="dim", no_wrap=True)

        trace_map: dict[str, list[str]] = {}
        for variable, mode, trace_id in self._traces:
            var_str = str(variable)
            trace_map.setdefault(var_str, []).append(f"{mode}:{trace_id[:12]}")

        for key, var in self._field_vars.items():
            traces = trace_map.get(str(var), [])
            var_tbl.add_row(
                key,
                type(var).__name__,
                repr(var.get()),
                ", ".join(traces) if traces else "—",
            )

        console.print(var_tbl)

        # ── Window geometry ──────────────────────────────────────────────
        geom = self._root.geometry()
        console.print(
            Panel(
                f"[bold]Geometry:[/bold] {geom}\n"
                f"[bold]Title:[/bold] {self._spec.title}\n"
                f"[bold]Min size:[/bold] {self._spec.min_width}×{self._spec.min_height}\n"
                f"[bold]Field count:[/bold] {len(self._spec.fields)}\n"
                f"[bold]Keyed vars:[/bold] {len(self._field_vars)}\n"
                f"[bold]Active traces:[/bold] {len(self._traces)}\n"
                f"[bold]Error labels:[/bold] {len(self._error_labels)}",
                title="Window Info",
                border_style="blue",
            )
        )
        console.print()

    def _debug_reload(self) -> None:
        """Tear down, rebuild the dialog content, and log the result.

        Called *after* modules have been reloaded and ``self.__class__``
        has been rebound, so this method always runs freshly-loaded code.
        """
        assert self._root is not None
        self._reload = True

        # ── 1. snapshot current field values ─────────────────────────────
        preserved: dict[str, Any] = {}
        for key, var in self._field_vars.items():
            preserved[key] = var.get()

        # ── 2. clean up Tk state ─────────────────────────────────────────
        self._remove_all_traces()
        self._field_vars.clear()
        self._field_widgets.clear()
        self._button_widgets.clear()
        self._field_rows.clear()
        self._error_labels.clear()
        self._first_focus = None

        for child in self._root.winfo_children():
            child.destroy()

        # ── 3. rebuild content with new code ─────────────────────────────
        self._build_content()

        # ── 4. restore preserved values ──────────────────────────────────
        for key, value in preserved.items():
            restored_var = self._field_vars.get(key)
            if restored_var is not None:
                restored_var.set(value)

        # ── 5. re-center and refresh ─────────────────────────────────────
        from .window import center_window as _center

        _center(self._root)
        self._root.update_idletasks()

    def _add_debug_buttons(self, action_bar_row: int) -> None:
        """
        Add DEBUG: Print and DEBUG: Refresh buttons below the action bar.
        """
        print(
            "Debug mode enabled: adding debug button for refreshing/updating the gui."
        )

        def _reload_and_rebuild() -> None:
            """Reload all gui modules, rebind the class, then call
            ``self._debug_reload()`` which now resolves to fresh code.

            This closure is captured once and never needs to change — the
            ``importlib.reload`` + class-rebinding logic is stable.  All
            mutable debug/rebuild logic lives in ``_debug_reload``, which
            is always called *after* the reload.
            """
            import importlib
            import sys

            gui_pkg = "cookiecutter_pypackage.scripts.gui"
            gui_dir = Path(__file__).parent
            submodules = [
                p.stem
                for p in gui_dir.iterdir()
                if p.is_file() and p.suffix == ".py" and not p.name.startswith("__")
            ]
            reloaded: list[str] = []
            for name in submodules:
                fqn = f"{gui_pkg}.{name}"
                mod = sys.modules.get(fqn)
                if mod is not None:
                    importlib.reload(mod)
                    reloaded.append(name)
            new_dialog_mod = sys.modules.get(f"{gui_pkg}.dialog")
            if new_dialog_mod is not None:
                new_cls = getattr(new_dialog_mod, "FormDialog", None)
                if new_cls is not None:
                    self.__class__ = new_cls  # type: ignore[assignment]

            # self._debug_reload() now resolves through the NEW class
            self._debug_reload()

            console.print(
                f"[bold green]✓ Dialog reloaded[/bold green]  "
                f"(modules: {', '.join(reloaded)})"
            )

        # ── debug separator ──────────────────────────────────────────────
        debug_sep_row = action_bar_row + 1
        sep = CTkSeparator(self._content)
        sep.grid(
            row=debug_sep_row,
            column=0,
            columnspan=3,
            sticky=ctk.EW,
            pady=(12, 12),
        )

        # ── debug button frame ───────────────────────────────────────────
        debug_btn_row = debug_sep_row + 1
        debug_frame = ctk.CTkFrame(self._content)
        debug_frame.grid(
            row=debug_btn_row,
            column=0,
            columnspan=3,
            sticky=ctk.EW,
            pady=(0, 0),
        )
        debug_frame.columnconfigure(0, weight=1)
        debug_frame.columnconfigure(3, weight=1)

        print_general_btn = ctk.CTkButton(
            debug_frame,
            text="DEBUG: Print",
            command=lambda: self._debug_print(),
        )
        # print_general_btn.grid(row=0, column=0, columnspan=1, padx=(7, 0), sticky=ctk.EW)
        print_general_btn.pack(side="left", fill="x", padx=(20, 2), expand=True)
        CreateToolTip(print_general_btn, "Print field state to console")
        self._button_widgets["debug_print"] = print_general_btn

        print_widget_data_btn = ctk.CTkButton(
            debug_frame,
            text="DEBUG: Widget Data",
            command=lambda: self._debug_widget_data(),
        )
        # print_widget_data_btn.grid(row=0, column=1, columnspan=1, padx=(7, 0), sticky=ctk.EW)
        print_widget_data_btn.pack(side="left", fill="x", padx=(2, 2), expand=True)
        CreateToolTip(
            print_widget_data_btn,
            "Print layout info for every widget to console (grids, packs, etc.)",
        )
        self._button_widgets["debug_widget_data"] = print_widget_data_btn

        refresh_btn = ctk.CTkButton(
            debug_frame,
            text="DEBUG: Refresh",
            command=_reload_and_rebuild,
        )
        # refresh_btn.grid(row=0, column=2, columnspan=1, padx=(7, 0), sticky=ctk.EW)
        refresh_btn.pack(side="left", fill="x", padx=(2, 20), expand=True)
        CreateToolTip(
            refresh_btn,
            "Rebuild the GUI while preserving field values (for testing dynamic updates)",
        )
        self._button_widgets["debug_refresh"] = refresh_btn


# ---------------------------------------------------------------------------
# Renderer dispatch table
# ---------------------------------------------------------------------------

_RENDERERS: dict[FieldKind, Callable[[FormDialog, FieldSpec, GridInfo], None]] = {
    FieldKind.LABEL: FormDialog._render_label,
    FieldKind.TEXT: FormDialog._render_text,
    FieldKind.SELECT: FormDialog._render_select,
    FieldKind.CHECKBOX: FormDialog._render_checkbox,
    FieldKind.BUTTON: FormDialog._render_button,
}
