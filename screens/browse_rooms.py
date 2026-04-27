# Room browsing and reservation booking screen for students.
# Validates nine rules before inserting: future date, same-day time, min/max duration,
# daily 3-hour cap, personal overlap, 2-hour cooldown, active rule set, room conflict, then insert.

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date, datetime, timedelta
import os
import pytz
from connect_db import execute_query

from components.date_picker import make_date_entry

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"
LIGHT  = "#F8F8F8"

TIME_SLOTS = [f"{h:02d}:{m:02d}" for h in range(7, 24) for m in (0, 30)]

CATEGORY_INFO = {
    "Projector Rooms": {
        "prefix":       "[P]",
        "tooltip_title": "Projector Rooms",
        "tooltip_body":  "2nd floor (211E, 211W)\nProjector equipped  ·  Max 20 users",
        "db_value":      "Projector Room",
    },
    "Group Study Rooms": {
        "prefix":       "[G]",
        "tooltip_title": "Group Study Rooms",
        "tooltip_body":  "2nd floor (207, 208) & 3rd floor (307, 308)\nCollaborative space  ·  Max 5 users",
        "db_value":      "Group Study Room",
    },
    "Single Study Rooms": {
        "prefix":       "[S]",
        "tooltip_title": "Single Study Rooms",
        "tooltip_body":  "3rd floor (326–336)\nQuiet individual study  ·  Max 1 user",
        "db_value":      "Single Study Room",
    },
}


# Follows the cursor so the tooltip never obscures the button it belongs to.
class FloatingTooltip:
    def __init__(self, widget, title, body):
        self.widget = widget
        self.title  = title
        self.body   = body
        self.tw     = None
        widget.bind("<Enter>",  self._show)
        widget.bind("<Leave>",  self._hide)
        widget.bind("<Motion>", self._follow)

    def _show(self, event=None):
        if self.tw:
            return
        x = event.x_root + 14
        y = event.y_root + 18
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        # Outer maroon border
        outer = tk.Frame(self.tw, bg=MAROON, padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        # White inner card
        inner = tk.Frame(outer, bg=WHITE, padx=14, pady=10)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=self.title,
                 fg=MAROON, bg=WHITE,
                 font=("Poppins", 11, "bold"),
                 anchor="w"
                 ).pack(anchor="w")
        tk.Frame(inner, bg="#E8E8E8", height=1).pack(fill="x", pady=(4, 6))
        tk.Label(inner, text=self.body,
                 fg="#444444", bg=WHITE,
                 font=("Poppins", 10),
                 justify="left", anchor="w"
                 ).pack(anchor="w")

    def _follow(self, event=None):
        if self.tw:
            self.tw.geometry(f"+{event.x_root + 14}+{event.y_root + 18}")

    def _hide(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


class BrowseRooms(tk.Frame):
    def __init__(self, parent, user_info: dict, navigator, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.user_info    = user_info
        self.navigator    = navigator
        self.selected_cat = None
        self._room_id_map = {}
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Scrollable content area
        content = tk.Frame(self, bg=WHITE)
        content.grid(row=0, column=0, sticky="nsew", padx=36, pady=24)
        content.columnconfigure(0, weight=1)

        # Page title
        tk.Label(content, text="Browse Rooms",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w")
        tk.Label(content, text="Select a room category to begin your reservation.",
                 fg="#666666", bg=WHITE, font=("Poppins", 12)
                 ).grid(row=1, column=0, sticky="w", pady=(2, 24))

        # ── Category buttons (centered, 70×200, rounded) ──────────────
        cat_outer = tk.Frame(content, bg=WHITE)
        cat_outer.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        cat_outer.columnconfigure(0, weight=1)
        cat_outer.columnconfigure(2, weight=1)

        cat_inner = tk.Frame(cat_outer, bg=WHITE)
        cat_inner.grid(row=0, column=1)

        self.cat_buttons = {}
        for cat_name, info in CATEGORY_INFO.items():
            label = f"{info['prefix']}  {cat_name}"
            btn = ctk.CTkButton(
                cat_inner,
                text=label,
                fg_color=MAROON,
                text_color=WHITE,
                hover_color="#7A1820",
                border_color=MAROON,
                border_width=0,
                corner_radius=12,
                height=70,
                width=200,
                font=("Poppins", 13, "bold"),
                cursor="hand2",
                command=lambda c=cat_name: self._select_category(c)
            )
            btn.pack(side="left", padx=14)
            FloatingTooltip(btn, info["tooltip_title"], info["tooltip_body"])
            self.cat_buttons[cat_name] = btn

        # Hint label
        self.hint_lbl = tk.Label(content, text="",
                                  fg="#888888", bg=WHITE,
                                  font=("Poppins", 11, "italic"))
        self.hint_lbl.grid(row=3, column=0, pady=(12, 0))

        # ── Reservation form card ────────────────────────────────────
        tk.Label(content, text="Reservation Details",
                 fg=MAROON, bg=WHITE, font=("Poppins", 14, "bold")
                 ).grid(row=4, column=0, sticky="w", pady=(24, 8))

        form_card = tk.Frame(content, bg=WHITE,
                              highlightbackground="#D0D0D0",
                              highlightthickness=1)
        form_card.grid(row=5, column=0, sticky="ew")

        form_inner = tk.Frame(form_card, bg=WHITE)
        form_inner.pack(fill="both", expand=True, padx=28, pady=22)
        form_inner.columnconfigure(1, weight=1)

        self._build_form(form_inner)

    def _build_form(self, f):
        row_pady = (0, 14)

        # Select Room
        tk.Label(f, text="Select Room:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12, "bold")
                 ).grid(row=0, column=0, sticky="w", pady=row_pady)
        self.room_var = tk.StringVar()
        self.room_combo = ttk.Combobox(f, textvariable=self.room_var,
                                        state="readonly", width=36,
                                        font=("Poppins", 12))
        self.room_combo.grid(row=0, column=1, sticky="w", padx=(14, 0), pady=row_pady)

        # Date — tkcalendar DateEntry (falls back to styled CTkEntry)
        tk.Label(f, text="Reservation Date:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12, "bold")
                 ).grid(row=1, column=0, sticky="w", pady=row_pady)

        today = date.today()
        self._date_widget = make_date_entry(
            f, default_date=today.strftime("%Y-%m-%d"), entry_width=160)
        self._date_widget.grid(row=1, column=1, sticky="w", padx=(14, 0), pady=row_pady)

        # Start Time
        tk.Label(f, text="Start Time:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12, "bold")
                 ).grid(row=2, column=0, sticky="w", pady=row_pady)
        self.start_var = tk.StringVar()
        ttk.Combobox(f, textvariable=self.start_var,
                      values=TIME_SLOTS, state="readonly", width=14,
                      font=("Poppins", 12)
                      ).grid(row=2, column=1, sticky="w", padx=(14, 0), pady=row_pady)

        # End Time
        tk.Label(f, text="End Time:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12, "bold")
                 ).grid(row=3, column=0, sticky="w", pady=row_pady)
        self.end_var = tk.StringVar()
        ttk.Combobox(f, textvariable=self.end_var,
                      values=TIME_SLOTS, state="readonly", width=14,
                      font=("Poppins", 12)
                      ).grid(row=3, column=1, sticky="w", padx=(14, 0), pady=row_pady)

        # Divider
        tk.Frame(f, bg="#E0E0E0", height=1
                 ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        # RESERVE button – full width, tall
        tk.Button(
            f, text="RESERVE ROOM",
            fg=WHITE, bg=MAROON,
            font=("Poppins", 14, "bold"),
            relief="flat", bd=0, pady=16, cursor="hand2",
            command=self._do_reserve
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(16, 0))

    # Highlights the selected category button and repopulates the room dropdown.
    def _select_category(self, cat_name):
        self.selected_cat = cat_name

        for name, btn in self.cat_buttons.items():
            if name == cat_name:
                btn.configure(fg_color=GOLD, text_color=MAROON,
                               hover_color="#D4A800")
            else:
                btn.configure(fg_color=MAROON, text_color=WHITE,
                               hover_color="#7A1820")

        db_val = CATEGORY_INFO[cat_name]["db_value"]
        try:
            rows = execute_query(
                "SELECT room_id, room_number, room_name, capacity FROM Rooms "
                "WHERE room_category = %s AND status = 'available'",
                (db_val,), fetch=True
            )
            self._room_id_map = {}
            values = []
            for r in rows:
                label = f"{r['room_number']} - {r['room_name']} (capacity: {r['capacity']})"
                values.append(label)
                self._room_id_map[label] = r["room_id"]

            self.room_combo["values"] = values
            if values:
                self.room_var.set(values[0])
                self.hint_lbl.config(
                    text=f"{len(values)} room(s) available in {cat_name}",
                    fg="#007700"
                )
            else:
                self.room_var.set("")
                self.hint_lbl.config(
                    text=f"No available rooms in {cat_name} at this time.",
                    fg="#CC0000"
                )
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _do_reserve(self):
        if not self.selected_cat:
            messagebox.showwarning("Reserve", "Please select a room category first.")
            return
        room_str  = self.room_var.get()
        date_str  = self._date_widget.get()
        start_str = self.start_var.get()
        end_str   = self.end_var.get()

        if not all([room_str, date_str, start_str, end_str]):
            messagebox.showwarning("Reserve", "Please fill in all fields.")
            return

        room_id = getattr(self, "_room_id_map", {}).get(room_str)
        if room_id is None:
            messagebox.showerror("Reserve", "Invalid room selection.")
            return

        if start_str >= end_str:
            messagebox.showerror("Reserve", "End time must be after start time.")
            return

        # 1. FUTURE DATE VALIDATION
        try:
            reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Reserve", "Invalid date format. Use YYYY-MM-DD.")
            return

        today = date.today()
        if reservation_date < today:
            messagebox.showerror(
                "Reserve",
                "Reservation date must be today or a future date."
            )
            return

        # 2. SAME-DAY BOOKING TIME VALIDATION — uses Detroit timezone since the library is local.
        if reservation_date == today:
            local_tz = pytz.timezone("America/Detroit")
            now_est = datetime.now(local_tz)
            current_time_str = now_est.strftime("%H:%M")
            if start_str <= current_time_str:
                messagebox.showerror(
                    "Invalid Time",
                    "Cannot book a room in the past. Please select a future time."
                )
                return

        # 3. BOOKING DURATION VALIDATION
        fmt      = "%H:%M"
        start_dt = datetime.strptime(start_str, fmt)
        end_dt   = datetime.strptime(end_str, fmt)
        duration_minutes = (end_dt - start_dt).seconds // 60

        if duration_minutes < 60:
            messagebox.showerror(
                "Invalid Duration",
                "Minimum booking duration is 1 hour (60 minutes)."
            )
            return

        if duration_minutes > 120:
            messagebox.showerror(
                "Invalid Duration",
                "Maximum booking duration is 2 hours (120 minutes)."
            )
            return

        uid = self.user_info["user_id"]

        try:
            # 4. DAILY 3-HOUR LIMIT
            daily = execute_query(
                "SELECT COALESCE(SUM(TIMESTAMPDIFF(MINUTE, start_time, end_time)), 0) AS total "
                "FROM Reservations "
                "WHERE user_id = %s AND reservation_date = %s "
                "AND status IN ('reserved', 'checked_in', 'completed')",
                (uid, date_str), fetch=True
            )
            total_booked = int(daily[0]["total"]) if daily else 0
            if total_booked + duration_minutes > 180:
                remaining = 180 - total_booked
                messagebox.showerror(
                    "Daily Limit Exceeded",
                    f"You have already booked {total_booked} min today.\n"
                    f"Only {remaining} min remaining (daily limit: 3 hours)."
                )
                return

            # 5. OVERLAPPING RESERVATION CHECK
            overlap = execute_query(
                "SELECT COUNT(*) AS cnt FROM Reservations "
                "WHERE user_id = %s AND reservation_date = %s "
                "AND status IN ('reserved', 'checked_in') "
                "AND NOT (end_time <= %s OR start_time >= %s)",
                (uid, date_str, start_str, end_str), fetch=True
            )
            if overlap and int(overlap[0]["cnt"]) > 0:
                messagebox.showerror(
                    "Overlapping Reservation",
                    "You cannot book two rooms at the same time.\n"
                    "Please choose a different time slot."
                )
                return

            # 6. 2-HOUR COOLDOWN AFTER CHECK-IN — MySQL TIME columns return timedelta objects.
            cooldown = execute_query(
                "SELECT r.end_time FROM Reservations r "
                "JOIN Check_Ins c ON c.reservation_id = r.reservation_id "
                "WHERE r.user_id = %s AND r.reservation_date = CURDATE() "
                "ORDER BY r.end_time DESC LIMIT 1",
                (uid,), fetch=True
            )
            if cooldown:
                last_end = cooldown[0]["end_time"]
                if hasattr(last_end, "seconds"):
                    last_end_dt = datetime.combine(
                        date.today(),
                        (datetime.min + last_end).time()
                    )
                else:
                    last_end_dt = datetime.combine(date.today(), last_end)
                cooldown_until = last_end_dt + timedelta(hours=2)
                now = datetime.now()
                if now < cooldown_until:
                    wait_min = int((cooldown_until - now).total_seconds() // 60)
                    messagebox.showerror(
                        "Cooldown Period",
                        f"A 2-hour cooldown is required after check-in.\n"
                        f"You can book again in {wait_min} minute(s)."
                    )
                    return

            # 7. FETCH ACTIVE RULE SET  (needed before both conflict check and insert)
            rule_result = execute_query(
                "SELECT rule_set_id FROM Rules WHERE is_active = 1 "
                "ORDER BY rule_set_id DESC LIMIT 1",
                fetch=True
            )
            if not rule_result:
                messagebox.showerror("Error", "No active rule set found.")
                return
            rule_set_id = rule_result[0]["rule_set_id"]

            # 8. ROOM CONFLICT CHECK (blocks double-booking by any student)
            room_number = room_str.split(" - ")[0]
            conflict = execute_query(
                "SELECT COUNT(*) AS conflict_count FROM Reservations "
                "WHERE room_id = %s AND reservation_date = %s "
                "AND status NOT IN ('cancelled', 'no_show') "
                "AND start_time < %s AND end_time > %s",
                (room_id, date_str, end_str, start_str), fetch=True
            )
            if conflict and int(conflict[0]["conflict_count"]) > 0:
                messagebox.showerror(
                    "Room Not Available",
                    f"Room {room_number} is not available from {start_str} to {end_str} "
                    f"on {date_str}. Please choose a different time or room."
                )
                return

            # 9. INSERT RESERVATION
            execute_query(
                """INSERT INTO Reservations
                   (user_id, room_id, reservation_date, start_time, end_time, status, rule_set_id)
                   VALUES (%s, %s, %s, %s, %s, 'reserved', %s)""",
                (uid, room_id, date_str, start_str, end_str, rule_set_id)
            )
            messagebox.showinfo("Reserved", "Reservation created successfully!")
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
