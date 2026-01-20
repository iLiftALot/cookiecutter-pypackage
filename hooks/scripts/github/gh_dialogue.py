import tkinter as tk
from collections.abc import Callable
from functools import singledispatch
from itertools import groupby
from tkinter import ttk
from typing import Unpack

from scripts.github.shared_types import (  # ty:ignore[unresolved-import]
    AnyField,
    ButtonField,
    CheckBoxField,
    ComboBoxField,
    FormInputs,
    FormResult,
    TextField,
    OrderedFormField,
    LabelField,
)

type AnyWidget = ttk.Button | tk.Entry | ttk.Combobox | tk.Checkbutton | tk.Label
"""Union of all possible widget types."""


class CreateToolTip(object):
    """
    Creates a tooltip for a given widget
    """

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.root = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event: tk.Event | None = None):
        self.show_tip()

    def leave(self, event: tk.Event | None = None):
        self.hide_tip()

    def show_tip(self):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + 30

        # Get the root window and temporarily disable its topmost
        self.root = self.widget.winfo_toplevel()
        self.root.attributes("-topmost", False)

        # Create tooltip window
        self.tip_window = tk.Toplevel()
        self.tip_window.wm_overrideredirect(True)  # removes window decorations
        self.tip_window.wm_geometry(f"+{x}+{y}")
        self.tip_window.attributes("-topmost", True)

        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#FFFFE0",
            foreground="#000000",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "10", "normal"),
        )
        label.pack(ipadx=1)

        self.tip_window.update_idletasks()
        self.tip_window.after(10000, self.hide_tip)  # auto-hide after 10 seconds

    def hide_tip(self, event: tk.Event | None = None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
        # Restore root's topmost attribute
        if self.root:
            self.root.attributes("-topmost", True)
            self.root = None


@singledispatch
def widget_factory(
    field: AnyField,
    root: tk.Tk,
    cb_fn: Callable[[], str | None] | None,
    frame: tk.Frame,
    field_key: str | None,
    field_vars: dict[str, tk.Variable],
) -> tuple[str | None, AnyWidget]:
    raise NotImplementedError(f"Unsupported field type: {type(field)}")


@widget_factory.register
def _(
    field: ButtonField,
    root: tk.Tk,
    cb_fn: Callable[[], str | None] | None,
    frame: tk.Frame,
    field_key: str | None,
    field_vars: dict[str, tk.Variable],
) -> tuple[str | None, AnyWidget]:
    btn_frame = frame
    i = frame.grid_size()[1]
    button_label, help_text, callback_function, bind_to = field
    updated_callback_function: Callable[[], None]
    target_key = normalize_key(bind_to) if bind_to else None

    if callable(callback_function):

        def action() -> None:
            result = callback_function()
            if target_key is None or result is None:
                return
            target_var = field_vars.get(target_key)
            if target_var is not None:
                target_var.set(result)

        updated_callback_function = action
    elif callback_function is None and callable(cb_fn):

        def wrapped_cb_fn() -> None:
            cb_fn()

        updated_callback_function = wrapped_cb_fn
    else:
        raise ValueError(
            "ButtonField callback_function must be a callable or None"
            f"... got {type(callback_function)} from {field.field_label}."
        )

    final_action = updated_callback_function
    btn = ttk.Button(btn_frame, text=button_label, command=final_action)
    btn.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
    CreateToolTip(btn, help_text)

    return field_key, btn


@widget_factory.register
def _(
    field: TextField,
    root: tk.Tk,
    cb_fn: Callable[[], str | None] | None,
    frame: tk.Frame,
    field_key: str | None,
    field_vars: dict[str, tk.Variable],
) -> tuple[str | None, AnyWidget]:
    text_field_frame = frame
    i = frame.grid_size()[1]

    text_field_label, default_value, help_text = field
    lbl = tk.Label(text_field_frame, text=text_field_label)
    lbl.grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)

    var = tk.StringVar(master=root, value=default_value)
    entry = tk.Entry(text_field_frame, textvariable=var)
    entry.grid(row=i, column=1, padx=10, pady=5)
    CreateToolTip(entry, help_text)
    if field_key is not None:
        field_vars[field_key] = var

    return field_key, entry


@widget_factory.register
def _(
    field: ComboBoxField,
    root: tk.Tk,
    cb_fn: Callable[[], str | None] | None,
    frame: tk.Frame,
    field_key: str | None,
    field_vars: dict[str, tk.Variable],
) -> tuple[str | None, AnyWidget]:
    combo_box_frame = frame
    i = frame.grid_size()[1]

    combobox_label, default_value, help_text, options = field
    lbl = tk.Label(combo_box_frame, text=combobox_label)
    lbl.grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
    var = tk.StringVar(master=root, value=default_value)
    combo = ttk.Combobox(combo_box_frame, values=options, textvariable=var)
    combo.grid(row=i, column=1, padx=10, pady=5)
    CreateToolTip(combo, help_text)
    if field_key is not None:
        field_vars[field_key] = var

    return field_key, combo


@widget_factory.register
def _(
    field: CheckBoxField,
    root: tk.Tk,
    cb_fn: Callable[[], str | None] | None,
    frame: tk.Frame,
    field_key: str | None,
    field_vars: dict[str, tk.Variable],
) -> tuple[str | None, AnyWidget]:
    check_box_frame = frame
    i = frame.grid_size()[1]
    checkbox_label, default_value, help_text = field
    var = tk.BooleanVar(master=root, value=bool(default_value))
    chk = tk.Checkbutton(check_box_frame, text=checkbox_label, variable=var)
    chk.grid(row=i, column=0, columnspan=2, padx=10, pady=5)
    CreateToolTip(chk, help_text)
    if field_key is not None:
        field_vars[field_key] = var

    return field_key, chk


@widget_factory.register
def _(
    field: LabelField,
    root: tk.Tk,
    cb_fn: Callable[[], str | None] | None,
    frame: tk.Frame,
    field_key: str | None,
    field_vars: dict[str, tk.Variable],
) -> tuple[str | None, AnyWidget]:
    label_frame = frame
    i = frame.grid_size()[1]
    label_label = field.field_label
    lbl = tk.Label(label_frame, text=label_label, font=("Arial", 12, "bold"))
    lbl.grid(row=i, column=0, columnspan=2, padx=10, pady=5)

    return None, lbl


def normalize_key(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned.lower().replace(" ", "_")


def resolve_field_key(
    ordered_field: OrderedFormField | None,
    field: AnyField,
) -> str | None:
    if ordered_field is not None and ordered_field.key:
        return normalize_key(ordered_field.key)
    if isinstance(field, (LabelField, ButtonField)):
        return None
    if hasattr(field, "field_label"):
        return normalize_key(field.field_label)
    return None


def show_form_dialog(
    title: str, subtitle: str, **fields: Unpack[FormInputs]
) -> FormResult:
    """Show a multi-field form dialog. fields = {label: default_value}"""
    result = FormResult()
    ordered_fields: list[OrderedFormField] | None = fields.get("ordered_fields", None)
    field_entries: dict[str, AnyWidget] = {}
    field_vars: dict[str, tk.Variable] = {}

    root = tk.Tk()
    root.title(title)
    subtitle_label = tk.Label(root, text=subtitle, font=("Arial", 14, "bold"))
    subtitle_label.grid(row=0, column=0, columnspan=2, pady=(10, 0))

    # set window on top
    root.attributes("-topmost", True)

    def on_submit() -> None:
        print("Form submitted successfully.")
        result.cancelled = False

        for field_key, widget in field_entries.items():
            if isinstance(widget, tk.Entry):
                result.config[field_key] = widget.get()
            elif isinstance(widget, ttk.Combobox):
                result.config[field_key] = widget.get()
            elif isinstance(widget, tk.Checkbutton):
                var = widget.cget("variable")
                result.config[field_key] = bool(root.getvar(var))

        root.destroy()

    def on_cancel() -> None:
        print("Form cancelled by user.")
        root.destroy()

    def get_default_callback(field_tuple: AnyField) -> Callable[[], None] | None:
        if (
            isinstance(field_tuple, ButtonField)
            and field_tuple.callback_function is None
        ):
            return (
                on_submit if field_tuple.field_label.lower() == "submit" else on_cancel
            )
        return None

    if ordered_fields:
        ordered_fields_sorted = sorted(
            ordered_fields,
            key=lambda field: (field.xy[0], field.xy[1]),
        )

        for row_key, row_fields in groupby(
            ordered_fields_sorted,
            key=lambda field: field.xy[0],
        ):
            row_frame = tk.Frame(root)
            row_frame.grid(
                row=row_key + 1,
                column=0,
                columnspan=2,
                pady=10,
                sticky=tk.W,
            )

            row_fields_list = list(row_fields)
            for col_key, col_fields in groupby(
                row_fields_list,
                key=lambda field: field.xy[1],
            ):
                cell_frame = tk.Frame(row_frame)
                cell_frame.grid(row=0, column=col_key, padx=10, pady=5, sticky=tk.W)

                for ordered_field in col_fields:
                    field = ordered_field.field_tuple
                    field_key = resolve_field_key(ordered_field, field)
                    widget_key, widget = widget_factory(
                        field,
                        root,
                        get_default_callback(field),
                        cell_frame,
                        field_key,
                        field_vars,
                    )
                    if widget_key is not None:
                        field_entries[widget_key] = widget
    else:
        frames: dict[AnyField, tuple[tk.Frame, int]] = {
            TextField: (tk.Frame(root), 1),
            ComboBoxField: (tk.Frame(root), 2),
            CheckBoxField: (tk.Frame(root), 3),
            ButtonField: (tk.Frame(root), 4),
        }

        for field_type, (frame, row) in frames.items():
            frame.grid(row=row, column=0, columnspan=2, pady=10)

        all_fields = [
            *[bf for bf in fields.get("button_fields", [])],
            *[tf for tf in fields.get("text_fields", [])],
            *[cb for cb in fields.get("combo_boxes", [])],
            *[chk for chk in fields.get("check_boxes", [])],
        ]

        for field in all_fields:
            field_key = resolve_field_key(None, field)
            widget_key, widget = widget_factory(
                field,
                root,
                get_default_callback(field),
                frames[type(field)][0],
                field_key,
                field_vars,
            )
            if widget_key is not None:
                field_entries[widget_key] = widget

    root.mainloop()
    return result
