import tkinter as tk
from typing import Callable

import customtkinter as ctk


class CreateToolTip:
    """
    Creates a tooltip for a given widget
    """

    def __init__(
        self,
        widget: ctk.CTkBaseClass,
        text: str,
        delay: int = 500,
        debug_cb: Callable[[ctk.CTkBaseClass, str], str] | None = None,
    ) -> None:
        self.debug_cb = debug_cb
        self.widget = widget
        self.text = text
        self.tip_window = None
        self._after_id: str | None = None  # tracks the pending after() call
        self._auto_hide_id: str | None = None
        self.delay = delay  # ms before tooltip appears

        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def __setattr__(self, name, value):
        if name == "text" and object.__getattribute__(self, "debug_cb"):
            debug_cb = object.__getattribute__(self, "debug_cb")
            widget = object.__getattribute__(self, "widget")
            if debug_cb and widget:
                value = debug_cb(widget, value)
        object.__setattr__(self, name, value)

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

        label = ctk.CTkLabel(self.tip_window, text=self.text)
        label.pack(ipadx=1)

        self.tip_window.update_idletasks()

        # auto-hide after 10 seconds
        self._auto_hide_id = self.tip_window.after(10000, self.hide_tip)

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
