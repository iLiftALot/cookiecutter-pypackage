import tkinter as tk
from tkinter import ttk


def on_submit(result, field_entries, root: tk.Tk) -> None:
    print("Form submitted successfully.")
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


def on_cancel(root: tk.Tk) -> None:
    print("Form cancelled by user.")
    root.destroy()
