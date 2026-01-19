import tkinter as tk
from tkinter import ttk
from typing import Unpack

from scripts.github.shared_types import (  # ty:ignore[unresolved-import]
    FormInputs,
    FormResult,
)


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


def show_form_dialog(
    title: str, subtitle: str, **fields: Unpack[FormInputs]
) -> FormResult:
    """Show a multi-field form dialog. fields = {label: default_value}"""
    result = FormResult()
    field_entries: dict[
        str,
        ttk.Button | tk.Entry | ttk.Combobox | tk.Checkbutton,
    ] = {}

    root = tk.Tk()
    root.title(title)
    subtitle_label = tk.Label(root, text=subtitle, font=("Arial", 14, "bold"))
    subtitle_label.grid(row=0, column=0, columnspan=2, pady=(10, 0))

    # set window on top
    root.attributes("-topmost", True)

    def on_submit() -> None:
        result.cancelled = False

        for field_label, widget in field_entries.items():
            # normalize field label to be used as dict key
            field_label = field_label.lower().replace(" ", "_")
            if isinstance(widget, tk.Entry):
                result.config[field_label] = widget.get()
            elif isinstance(widget, ttk.Combobox):
                result.config[field_label] = widget.get()
            elif isinstance(widget, tk.Checkbutton):
                var = widget.cget("variable")
                result.config[field_label] = bool(root.getvar(var))

        root.destroy()

    def on_cancel() -> None:
        root.destroy()

    button_fields = fields.get("button_fields", [])
    text_fields = fields.get("text_fields", [])
    combo_boxes = fields.get("combo_boxes", [])
    check_boxes = fields.get("check_boxes", [])

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
    text_field_frame = tk.Frame(root)
    text_field_frame.grid(row=1, column=0, columnspan=2, pady=10)
    combo_box_frame = tk.Frame(root)
    combo_box_frame.grid(row=2, column=0, columnspan=2, pady=10)
    check_box_frame = tk.Frame(root)
    check_box_frame.grid(row=3, column=0, columnspan=2, pady=10)

    for i, (button_label, help_text, callback_function) in enumerate(button_fields):
        action = callback_function or (
            on_submit if button_label.lower() == "submit" else on_cancel
        )
        btn = ttk.Button(btn_frame, text=button_label, command=action)
        btn.pack(side=tk.LEFT, padx=5)
        field_entries[button_label] = btn
        CreateToolTip(btn, help_text)

    for i, (field_label, default_value, help_text) in enumerate(text_fields):
        lbl = tk.Label(text_field_frame, text=field_label)
        lbl.grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
        entry = tk.Entry(text_field_frame)
        entry.insert(0, default_value)
        entry.grid(row=i, column=1, padx=10, pady=5)
        field_entries[field_label] = entry
        CreateToolTip(entry, help_text)

    for i, (field_label, default_value, help_text, options) in enumerate(combo_boxes):
        lbl = tk.Label(combo_box_frame, text=field_label)
        lbl.grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
        combo = ttk.Combobox(combo_box_frame, values=options)
        combo.set(default_value)
        combo.grid(row=i, column=1, padx=10, pady=5)
        field_entries[field_label] = combo
        CreateToolTip(combo, help_text)

    for i, (field_label, default_value, help_text) in enumerate(check_boxes):
        var = tk.IntVar(value=int(default_value))
        chk = tk.Checkbutton(check_box_frame, text=field_label, variable=var)
        chk.grid(row=i, column=0, columnspan=2, padx=10, pady=5)
        field_entries[field_label] = chk
        CreateToolTip(chk, help_text)

    root.mainloop()
    return result
