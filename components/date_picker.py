# Custom date picker that avoids the tkcalendar DateEntry double-click-close bug on Windows.
# tkcalendar's DateEntry widget closes immediately on the second click on Windows because
# the click-outside handler fires before the selection registers. This replacement uses
# a plain Toplevel popup so click handling is under our control.
#
# Usage:
#   frame = make_date_entry(parent, default_date="2025-01-01")
#   frame.pack(side="left", ...)
#   date_str = frame.get()   # returns "YYYY-MM-DD"

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from tkcalendar import Calendar

MAROON = "#5E1219"
GOLD   = "#EFBF04"
WHITE  = "#FFFFFF"
BLACK  = "#000000"


# Returns a tk.Frame with .get() and .entry attributes so callers treat it like an entry widget.
def make_date_entry(parent, default_date=None, entry_width=120, **kwargs):
    bg = kwargs.pop("bg", WHITE)
    frame = tk.Frame(parent, bg=bg, **kwargs)

    entry = ctk.CTkEntry(
        frame,
        width=entry_width,
        height=32,
        corner_radius=6,
        border_color=MAROON,
        border_width=1,
        fg_color=WHITE,
        text_color=BLACK,
        font=("Poppins", 12),
        placeholder_text="YYYY-MM-DD",
    )
    entry.pack(side="left")

    if default_date:
        entry.delete(0, "end")
        entry.insert(0, str(default_date))

    # List used as a mutable container so inner closures can replace the reference.
    _popup = [None]

    def open_calendar():
        # Second click on the icon closes the popup rather than opening a second one.
        if _popup[0] is not None:
            try:
                _popup[0].destroy()
            except Exception:
                pass
            _popup[0] = None
            return

        top = tk.Toplevel()
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        _popup[0] = top

        # Position the popup directly below the entry field.
        entry.update_idletasks()
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        top.geometry(f"+{x}+{y}")

        cal = Calendar(
            top,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            background=MAROON,
            foreground=WHITE,
            selectbackground=GOLD,
            selectforeground=MAROON,
            headersbackground="#3D0A0F",
            headersforeground=WHITE,
            normalforeground=BLACK,
            weekendforeground=MAROON,
            font=("Poppins", 10),
        )
        cal.pack(padx=5, pady=5)

        # Sync the calendar highlight with whatever the user typed before opening.
        cur = entry.get().strip()
        if cur:
            try:
                cal.set_date(cur)
            except Exception:
                pass

        def on_select(_event=None):
            entry.delete(0, "end")
            entry.insert(0, cal.get_date())
            try:
                top.destroy()
            except Exception:
                pass
            _popup[0] = None

        cal.bind("<<CalendarSelected>>", on_select)

        tk.Button(
            top, text="Select",
            bg=MAROON, fg=WHITE,
            font=("Poppins", 11, "bold"),
            relief="flat", cursor="hand2",
            command=on_select,
        ).pack(fill="x", padx=5, pady=(0, 5))

        # Bind to the root window so clicks anywhere outside the popup dismiss it.
        def close_on_outside(event):
            try:
                if top.winfo_exists():
                    wx = top.winfo_rootx()
                    wy = top.winfo_rooty()
                    ww = top.winfo_width()
                    wh = top.winfo_height()
                    inside = (wx <= event.x_root <= wx + ww
                              and wy <= event.y_root <= wy + wh)
                    if not inside:
                        top.destroy()
                        _popup[0] = None
            except Exception:
                pass

        top.winfo_toplevel().bind("<Button-1>", close_on_outside, add="+")

    tk.Button(
        frame, text="📅",
        bg=bg, relief="flat",
        font=("Arial", 13),
        cursor="hand2",
        command=open_calendar,
    ).pack(side="left", padx=(3, 0))

    # Attach .get() and .entry so callers can treat the frame like a plain entry widget.
    frame.get   = entry.get
    frame.entry = entry

    return frame
