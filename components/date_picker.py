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
        # FIX 4: destroy any previously tracked popup before opening a new one.
        if hasattr(entry, '_calendar_popup'):
            try:
                if entry._calendar_popup.winfo_exists():
                    entry._calendar_popup.destroy()
            except Exception:
                pass

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
        entry._calendar_popup = top  # FIX 4: track so navigation-away can clean up.

        # FIX 1: Close popup when any ancestor frame/screen is destroyed.
        def on_parent_destroy(event=None):
            try:
                if top.winfo_exists():
                    top.destroy()
            except Exception:
                pass

        parent = entry.master
        while parent and not isinstance(parent, (tk.Toplevel, tk.Tk)):
            parent.bind('<Destroy>', on_parent_destroy, add='+')
            parent = parent.master

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

        def confirm_date():
            try:
                if not entry.winfo_exists():
                    try:
                        top.destroy()
                    except Exception:
                        pass
                    return
                selected_date = cal.selection_get()
                formatted = selected_date.strftime("%Y-%m-%d")
                entry.delete(0, "end")
                entry.insert(0, formatted)
                try:
                    top.destroy()
                except Exception:
                    pass
                _popup[0] = None
            except Exception:
                try:
                    top.destroy()
                except Exception:
                    pass

        def cancel_calendar():
            try:
                top.destroy()
            except Exception:
                pass
            _popup[0] = None

        btn_frame = tk.Frame(top, bg=WHITE)
        btn_frame.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkButton(
            btn_frame,
            text="Confirm Date",
            width=130, height=32,
            fg_color="#5E1219",
            hover_color="#7A1A23",
            text_color="white",
            font=("Poppins", 11, "bold"),
            command=confirm_date,
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=90, height=32,
            fg_color="#888888",
            hover_color="#666666",
            text_color="white",
            font=("Poppins", 11),
            command=cancel_calendar,
        ).pack(side="right")

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
