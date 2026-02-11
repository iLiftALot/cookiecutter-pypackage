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
from tkinter import messagebox, ttk
from typing import Any, Literal, NamedTuple, overload

from ...run import console
from .result import FormResult
from .spec import FieldKind, FieldSpec, FormSpec, TkFont
from .tooltip import CreateToolTip
from .validation import ValidationIssue, ValidationResult, ValidationStatus
from .window import bring_to_front_briefly, center_window

# ---------------------------------------------------------------------------
# Widget type alias
# ---------------------------------------------------------------------------

type _AnyWidget = ttk.Button | ttk.Entry | ttk.Combobox | ttk.Checkbutton | ttk.Label
type _TraceMode = Literal["array", "read", "write", "unset"]


class ColumnInfo(NamedTuple):
    column: int
    columnspan: int


# ---------------------------------------------------------------------------
# FormDialog
# ---------------------------------------------------------------------------


class FormDialog:
    """Renders a :class:`FormSpec` as a modal ``Toplevel`` dialog.

    Call :meth:`show` to display the dialog and block until the user submits
    or cancels.  Returns a :class:`FormResult`.
    """

    def __init__(
        self, spec: FormSpec, debug: bool = False, reload: bool = False
    ) -> None:
        self._spec = spec
        self._result = FormResult()
        self._debug = debug
        self._reload = reload

        # Internal state — populated during ``show()``
        self._root: tk.Tk | None = None
        self._dialog: tk.Toplevel | tk.Tk | None = None
        self._content: ttk.Frame | None = None
        self._field_vars: dict[str, tk.Variable] = {}
        self._field_widgets: dict[str, _AnyWidget] = {}
        self._field_rows: dict[str, int] = {}
        self._button_widgets: dict[str, ttk.Button] = {}
        self._error_labels: dict[str, ttk.Label] = {}
        self._first_focus: tk.Widget | None = None
        self._traces: list[tuple[tk.Variable, _TraceMode, str]] = []

    # -- public API --------------------------------------------------------

    def show(self) -> FormResult:
        """Display the dialog modally and return the collected result."""
        # Use Tk() directly as the dialog window — on macOS, a Toplevel
        # transient to a withdrawn root renders blank.
        self._root = tk.Tk()
        self._root.title(self._spec.title)
        self._root.minsize(self._spec.min_width, self._spec.min_height)
        self._root.resizable(True, False)
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        # disable full screen on macOS (buggy with modals)
        # self._root.attributes("-fullscreen", False)

        # _dialog points to the same window for rendering convenience
        self._dialog = self._root

        self._build_content()

        # Cancel semantics
        self._root.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._root.bind("<Escape>", lambda _e: self._on_cancel())
        # Submit on Enter
        self._root.bind("<Return>", lambda _e: self._on_submit())
        # Clicking anywhere focuses the clicked widget (for better keyboard navigation)
        self._root.bind_all(
            "<Button-1>",
            lambda event: (
                event.widget.focus_set()
                if isinstance(event.widget, tk.Widget)
                else None
            ),
            add="+",
        )

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

    # -- layout ------------------------------------------------------------

    def _build_content(self) -> None:
        """Build a flat grid so label / entry / button columns align across
        all rows.  Action buttons (Submit, Cancel, …) are collected into a
        compact right-aligned bar separated from the form fields.
        """
        assert self._dialog is not None

        # ── outer content frame ──────────────────────────────────────────
        self._content = ttk.Frame(self._dialog, padding=(20, 16, 20, 12))
        self._content.grid(row=0, column=0, sticky="nsew")
        #   col 0 = labels   (fixed)
        #   col 1 = entries   (stretches)
        #   col 2 = aux buttons like "Browse…"  (fixed)
        #   col 3 = action buttons like "Submit" (in the button bar, handled separately)
        self._content.columnconfigure(0, weight=0)
        self._content.columnconfigure(1, weight=1)
        self._content.columnconfigure(2, weight=0)

        # ── partition fields ─────────────────────────────────────────────
        form_fields: list[FieldSpec] = []
        action_buttons: list[FieldSpec] = []

        if self._reload and not self._debug:
            self._debug = True

        # Filter out stale debug FieldSpecs injected by a previous reload
        self._spec.fields[:] = [
            f
            for f in self._spec.fields
            if not f.label.startswith("DEBUG:")
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
            sep_row = (max(f.row for f in self._spec.fields) + 1) * 2
            sep = ttk.Separator(self._content, orient="horizontal")
            sep.grid(
                row=sep_row,
                column=0,
                columnspan=3,
                sticky=tk.EW,
                pady=(12, 12),
            )

            btn_row = sep_row + 1
            btn_frame = ttk.Frame(self._content)
            btn_frame.grid(
                row=btn_row,
                column=0,
                columnspan=3,
                sticky=tk.NSEW,
                pady=(0, 0),
            )

            for idx, btn_spec in enumerate(action_buttons, 0):
                cb = self._resolve_button_callback(btn_spec)
                btn = ttk.Button(btn_frame, text=btn_spec.label, command=cb)
                padx = (0, 0) if idx == 0 else (8, 0)
                btn.grid(row=0, column=idx, padx=padx, sticky=tk.EW)
                # Track for debug output
                btn_key = btn_spec.label.lower().replace(" ", "_").replace(":", "")
                self._button_widgets[btn_key] = btn
                if btn_spec.help_text:
                    CreateToolTip(btn, btn_spec.help_text)

        # ── debug buttons (below the action bar) ─────────────────────────
        if self._debug:
            self._add_debug_buttons(btn_row)

    # -- field rendering ---------------------------------------------------

    def _render_field(self, spec: FieldSpec) -> None:
        """Render a single :class:`FieldSpec` into *parent*."""
        renderer = _RENDERERS.get(spec.kind)
        if renderer is None:
            raise ValueError(f"Unsupported field kind: {spec.kind}")
        col = 1
        colspan = 1
        if spec.kind in (FieldKind.TEXT, FieldKind.SELECT):
            if not spec.label and not spec.is_bound:
                # Standalone text field without a label or button
                # - stretch across entire width.
                col = 0
                colspan = 3
            elif not spec.label and spec.is_bound:
                # No label but bound to a button (e.g. Browse…)
                # — leave space for the button on the right
                col = 0
                colspan = 2
            elif spec.label and not spec.is_bound:
                # Label on the left but no button on the right
                # — stretch to the right edge
                col = 1
                colspan = 2
        elif spec.kind == FieldKind.LABEL:
            # Labels always stretch full width
            # — they are section headers, not field labels.
            col = 0
            colspan = 3
        elif spec.kind == FieldKind.CHECKBOX:
            # Checkboxes always sit in the label column on the left
            col = 0
            colspan = 2
        else:
            # BUTTON fields
            col = 2
            colspan = 1

        renderer(self, spec, ColumnInfo(col, colspan))

    def _render_label(self, spec: FieldSpec, column_info: ColumnInfo) -> None:
        grid_row = spec.row * 2
        font = spec.font if spec.font else TkFont().value
        column = column_info.column
        columnspan = column_info.columnspan
        lbl = ttk.Label(self._content, text=spec.label, font=font)
        lbl.grid(
            row=grid_row,
            column=column,
            columnspan=columnspan,
            padx=(4, 4),
            pady=(10, 2),
            sticky=tk.EW,
            # Position text in the middle
            anchor=tk.CENTER,
        )

    def _render_text(
        self,
        spec: FieldSpec,
        column_info: ColumnInfo,
        is_bound: bool = False,
    ) -> None:
        grid_row = spec.row * 2

        if spec.label:
            lbl = ttk.Label(self._content, text=spec.label)
            lbl.grid(row=grid_row, column=0, sticky=tk.W, padx=(4, 8), pady=5)

        var = tk.StringVar(master=self._root, value=spec.default or "")
        entry = ttk.Entry(self._content, textvariable=var)
        column = column_info.column
        columnspan = column_info.columnspan

        entry.grid(
            row=grid_row,
            column=column,
            columnspan=columnspan,
            padx=(0, 0),
            pady=5,
            sticky=tk.W if is_bound else tk.EW,
        )
        # Select all text on focus
        entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))

        if not spec.help_text:
            tooltip = CreateToolTip(entry, var.get())
            self._trace(var, "write", obj=tooltip, attr="text")
        else:
            CreateToolTip(entry, spec.help_text)
        if spec.key:
            self._field_vars[spec.key] = var
            self._field_widgets[spec.key] = entry
            self._field_rows[spec.key] = grid_row
        if self._first_focus is None:
            self._first_focus = entry

    def _render_select(self, spec: FieldSpec, column_info: ColumnInfo) -> None:
        grid_row = spec.row * 2

        if spec.label:
            lbl = ttk.Label(self._content, text=spec.label)
            lbl.grid(row=grid_row, column=0, sticky=tk.W, padx=(4, 8), pady=5)

        var = tk.StringVar(master=self._root, value=spec.default or "")
        state = "readonly" if spec.readonly else "normal"
        combo = ttk.Combobox(
            self._content,
            values=spec.options,
            textvariable=var,
            state=state,
        )
        column = column_info.column
        columnspan = column_info.columnspan
        combo.grid(
            row=grid_row,
            column=column,
            columnspan=columnspan,
            padx=(0, 0),
            pady=5,
            sticky=tk.EW,
        )

        if not spec.help_text:
            tooltip = CreateToolTip(combo, var.get())
            self._trace(var, "write", obj=tooltip, attr="text")
        else:
            CreateToolTip(combo, spec.help_text)
        if spec.key:
            self._field_vars[spec.key] = var
            self._field_widgets[spec.key] = combo
            self._field_rows[spec.key] = grid_row
        if self._first_focus is None:
            self._first_focus = combo

    def _render_checkbox(self, spec: FieldSpec, column_info: ColumnInfo) -> None:
        grid_row = spec.row * 2

        var = tk.BooleanVar(master=self._root, value=bool(spec.default))
        chk = ttk.Checkbutton(self._content, text=spec.label, variable=var)
        column = column_info.column
        columnspan = column_info.columnspan
        chk.grid(
            row=grid_row,
            column=column,
            columnspan=columnspan,
            padx=4,
            pady=5,
            sticky=tk.W,
        )

        if spec.help_text:
            CreateToolTip(chk, spec.help_text)
        if spec.key:
            self._field_vars[spec.key] = var
            self._field_widgets[spec.key] = chk

    def _render_button(self, spec: FieldSpec, column_info: ColumnInfo) -> None:
        """Render an *auxiliary* button (e.g. Browse…) bound to a field.

        Standalone action buttons (Submit / Cancel) are handled directly
        by :meth:`_build_content` and never reach this renderer.
        """
        target_key = spec.bind_to
        if not target_key:
            return  # safety — should not happen

        # Resolve the grid row of the field this button is bound to
        target_grid_row = self._field_rows.get(target_key, spec.row * 2)

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
        column = column_info.column
        columnspan = column_info.columnspan
        btn = ttk.Button(self._content, text=spec.label, command=callback)
        btn.grid(
            row=target_grid_row,
            column=column,
            columnspan=columnspan,
            padx=(0, 0),
            pady=5,
            sticky=tk.W,
        )

        # Track for debug output
        btn_key = spec.label.lower().replace(" ", "_").replace(":", "")
        self._button_widgets[btn_key] = btn
        if spec.help_text:
            CreateToolTip(btn, spec.help_text)

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
            assert self._dialog is not None
            proceed = messagebox.askyesno(
                "Warning",
                f"The following warnings were found:\n\n{msgs}\n\nProceed anyway?",
                parent=self._dialog,
            )
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
    def _trace(
        self,
        variable: tk.Variable,
        mode: Literal["array", "read", "write", "unset"],
        *,
        obj: object,
        attr: str,
    ) -> str: ...
    @overload
    def _trace(
        self,
        variable: tk.Variable,
        mode: Literal["array", "read", "write", "unset"],
        *,
        callback: Callable[..., object],
    ) -> str: ...
    def _trace(
        self,
        variable: tk.Variable,
        mode: Literal["array", "read", "write", "unset"],
        *,
        obj: object | None = None,
        attr: str | None = None,
        callback: Callable[..., object] | None = None,
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
            def _(*_args) -> None:
                setattr(obj, attr, variable.get())
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
            except tk.TclError:
                pass  # already gone
        self._traces.clear()

    def _get_lowest_available_row(self) -> int:
        """Calculate the lowest available grid row index for debug buttons."""
        return max(f.row for f in self._spec.fields) + 1

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
            parent = widget.master
            # In the flat grid, fields sit at grid_row (= spec.row * 2).
            # The slot immediately below (grid_row + 1) is reserved for errors.
            grid_row = widget.grid_info().get("row", 0)
            err_lbl = ttk.Label(
                parent,
                text=issue.message,
                foreground="red",
                font=("Arial", 10),
            )
            err_lbl.grid(
                row=grid_row + 1,
                column=1,
                columnspan=2,
                sticky=tk.W,
                padx=(0, 4),
            )
            self._error_labels[issue.field_key] = err_lbl

    def _clear_errors(self) -> None:
        """Remove all currently displayed inline error labels."""
        for lbl in self._error_labels.values():
            lbl.destroy()
        self._error_labels.clear()

    # -- debug ------------------------------------------------------------

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
        tbl.add_column("Value", style="green")
        tbl.add_column("Default", style="dim")
        tbl.add_column("Row", justify="right")
        tbl.add_column("Col", justify="right")
        tbl.add_column("Widget", style="dim cyan", no_wrap=True)
        tbl.add_column("Grid Info", style="dim")

        values = self._collect_var_values()

        for spec in sorted(self._spec.fields, key=lambda f: (f.row, f.col)):
            key = spec.key or spec.label or "—"
            value = str(values.get(spec.key, "—")) if spec.key else "—"
            # Look up keyed field widgets first, then button widgets by label
            widget: _AnyWidget | None = None
            if spec.key:
                widget = self._field_widgets.get(spec.key)
            if widget is None and spec.kind == FieldKind.BUTTON:
                btn_key = spec.label.lower().replace(" ", "_").replace(":", "")
                widget = self._button_widgets.get(btn_key)
            widget_class = type(widget).__name__ if widget else "—"
            grid_info = ""
            if widget is not None:
                gi = widget.grid_info()
                grid_info = (
                    f"column={gi.get('column')}, "
                    f"columnspan={gi.get('columnspan')}, "
                    f"row={gi.get('row')}, "
                    f"padx={gi.get('padx')}, "
                    f"pady={gi.get('pady')}, "
                    f"sticky={gi.get('sticky')}"
                )

            tbl.add_row(
                key,
                spec.kind.value,
                spec.label,
                value,
                str(spec.default) if spec.default is not None else "—",
                str(spec.row),
                str(spec.col),
                widget_class,
                grid_info,
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
        var_tbl.add_column("Trace IDs", style="dim")

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
        sep = ttk.Separator(self._content, orient="horizontal")
        sep.grid(
            row=debug_sep_row,
            column=0,
            columnspan=3,
            sticky=tk.EW,
            pady=(12, 12),
        )

        # ── debug button frame ───────────────────────────────────────────
        debug_btn_row = debug_sep_row + 1
        debug_frame = ttk.Frame(self._content)
        debug_frame.grid(
            row=debug_btn_row,
            column=0,
            columnspan=3,
            sticky=tk.NSEW,
            pady=(0, 0),
        )

        print_btn = ttk.Button(
            debug_frame,
            text="DEBUG: Print",
            command=lambda: self._debug_print(),
        )
        print_btn.grid(row=0, column=0, padx=(0, 0), sticky=tk.EW)
        CreateToolTip(print_btn, "Print field state to console")
        self._button_widgets["debug_print"] = print_btn

        refresh_btn = ttk.Button(
            debug_frame,
            text="DEBUG: Refresh",
            command=_reload_and_rebuild,
        )
        refresh_btn.grid(row=0, column=1, padx=(8, 0), sticky=tk.EW)
        CreateToolTip(
            refresh_btn,
            "Rebuild the GUI while preserving field values (for testing dynamic updates)",
        )
        self._button_widgets["debug_refresh"] = refresh_btn


# ---------------------------------------------------------------------------
# Renderer dispatch table
# ---------------------------------------------------------------------------

_RENDERERS: dict[FieldKind, Callable[[FormDialog, FieldSpec, ColumnInfo], None]] = {
    FieldKind.LABEL: FormDialog._render_label,
    FieldKind.TEXT: FormDialog._render_text,
    FieldKind.SELECT: FormDialog._render_select,
    FieldKind.CHECKBOX: FormDialog._render_checkbox,
    FieldKind.BUTTON: FormDialog._render_button,
}
