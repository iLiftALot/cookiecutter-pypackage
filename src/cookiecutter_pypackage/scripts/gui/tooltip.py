import tkinter as tk
from tkinter import ttk


class CreateToolTip(object):
    """
    Creates a tooltip for a given widget
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500) -> None:
        self.widget = widget
        self.text = text
        self.tip_window = None
        self._after_id: str | None = None  # tracks the pending after() call
        self._auto_hide_id: str | None = None
        self.delay = delay  # ms before tooltip appears
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event: tk.Event | None = None):
        self._after_id = self.widget.after(self.delay, self.show_tip)

    def leave(self, event: tk.Event | None = None):
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        self.hide_tip()

    def show_tip(self):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        # Create tooltip window
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)  # removes window decorations
        self.tip_window.wm_geometry(f"+{x}+{y}")
        self.tip_window.attributes("-topmost", True)
        self.tip_window.transient(self.widget.winfo_toplevel())

        label = ttk.Label(self.tip_window, text=self.text)
        label.pack(ipadx=1)

        self.tip_window.update_idletasks()
        # auto-hide after 10 seconds
        self._auto_hide_id = self.tip_window.after(
            10000, self.hide_tip
        )

    def hide_tip(self, event: tk.Event | None = None):
        if self._auto_hide_id is not None:
            self.widget.after_cancel(self._auto_hide_id)
            self._auto_hide_id = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except tk.TclError:
                pass
            self.tip_window = None

