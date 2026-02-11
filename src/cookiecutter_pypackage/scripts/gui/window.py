"""Tk/ttk window management utilities.

Provides helpers for centering, modality, brief ``-topmost`` focus strategy
on macOS, and parented file-dialog wrappers.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog


def center_window(window: tk.Toplevel | tk.Tk) -> None:
    """Center *window* on screen based on its requested geometry."""
    window.update_idletasks()
    width = max(window.winfo_reqwidth(), window.winfo_width())
    height = max(window.winfo_reqheight(), window.winfo_height())
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def bring_to_front_briefly(window: tk.Toplevel | tk.Tk) -> None:
    """Bring *window* to the front using a brief ``-topmost`` strategy.

    Sets ``-topmost`` to ``True``, calls ``lift()`` and ``focus_force()``,
    then schedules ``-topmost`` back to ``False`` after the window is visible.
    This avoids the persistent always-on-top annoyance while still reliably
    raising the window on macOS.
    """
    window.attributes("-topmost", True)
    window.lift()
    window.focus_force()
    # Unset topmost after the window has been presented
    window.after(200, lambda: window.attributes("-topmost", False))


def make_modal(dialog: tk.Toplevel, parent: tk.Tk) -> None:
    """Make *dialog* modal relative to *parent*.

    Sets the transient parent, grabs input focus, and waits for the dialog
    window to be destroyed before returning control.
    """
    dialog.transient(parent)
    dialog.grab_set()
    parent.wait_window(dialog)


def ask_directory(
    parent: tk.Toplevel | tk.Tk,
    *,
    initial_dir: str | None = None,
    title: str = "Select Directory",
) -> str | None:
    """Open a directory picker parented to *parent*.

    Parenting avoids the file dialog appearing behind the modal on macOS.
    Returns the selected path, or ``None`` if cancelled.
    """
    result = filedialog.askdirectory(
        parent=parent,
        initialdir=initial_dir,
        mustexist=True,
        title=title,
    )
    return result if result else None
