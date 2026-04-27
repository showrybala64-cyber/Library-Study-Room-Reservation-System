# Student dashboard with stat cards and embedded matplotlib charts.
# Agg backend is required because matplotlib is driven from a background thread context
# in some environments; using Agg prevents a "cannot call into Tcl from non-main thread" error.

import tkinter as tk
from tkinter import ttk
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import Patch

from connect_db import execute_query

MAROON     = "#5E1219"
GOLD       = "#EFBF04"
BLACK      = "#000000"
WHITE      = "#FFFFFF"
LIGHT_GOLD = "#FFF8E7"
GREEN      = "#2ecc71"
ORANGE     = "#e67e22"
RED        = "#e74c3c"


# MySQL TIME columns come back as timedelta objects, not strings.
def _time_to_hours(t):
    if hasattr(t, "seconds"):
        return t.seconds / 3600
    parts = str(t).split(":")
    return int(parts[0]) + int(parts[1]) / 60


class StudentDashboard(tk.Frame):
    def __init__(self, parent, user_info: dict, navigator, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.user_info        = user_info
        self.navigator        = navigator
        self._uid             = user_info.get("user_id")
        self._bar_widget      = None
        self._line_widget     = None
        self._timeline_widget = None
        self._charts_frame    = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        self._scroll_frame = tk.Frame(self._canvas, bg=WHITE)
        self._scroll_win   = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw"
        )

        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>",       self._on_canvas_configure)

        # Mousewheel is captured only while the cursor is over the canvas to avoid
        # interfering with comboboxes or other scrollable widgets on the same screen.
        self._canvas.bind("<Enter>", self._on_canvas_enter)
        self._canvas.bind("<Leave>", self._on_canvas_leave)

        self._build_content()

        # Recursively bind mousewheel to every widget already built
        self._bind_mousewheel_recursive(self)

    def _on_frame_configure(self, _event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._scroll_win, width=event.width)

    def _on_mousewheel(self, event):
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _on_canvas_enter(self, _event):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_leave(self, _event):
        self._canvas.unbind_all("<MouseWheel>")

    def _bind_mousewheel_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _build_content(self):
        sf = self._scroll_frame
        sf.columnconfigure(0, weight=1)
        self._sf = sf

        tk.Label(sf, text="Student Dashboard",
                 fg=MAROON, bg=WHITE, font=("Poppins", 24, "bold")
                 ).grid(row=0, column=0, sticky="w", padx=30, pady=(20, 0))

        name = self.user_info.get("name", "Student")
        tk.Label(sf, text=f"Welcome Back, {name}!",
                 fg="#333333", bg=WHITE, font=("Poppins", 14)
                 ).grid(row=1, column=0, sticky="w", padx=30, pady=(4, 18))

        cards_frame = tk.Frame(sf, bg=WHITE)
        cards_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 18))
        self._build_stat_cards(cards_frame)

        filter_frame = tk.Frame(sf, bg=WHITE)
        filter_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 18))
        self._build_filter_panel(filter_frame)

        # Charts are in a separate frame so they can be destroyed and rebuilt when filters change.
        self._rebuild_charts()

        upcoming_frame = tk.Frame(sf, bg=WHITE)
        upcoming_frame.grid(row=5, column=0, sticky="ew", padx=30, pady=(0, 30))
        upcoming_frame.columnconfigure(0, weight=1)
        self._upcoming_frame = upcoming_frame
        self._build_upcoming()

    # Tears down old chart widgets and redraws with current filter state.
    # Destroying and recreating is simpler than trying to update figures in place.
    def _rebuild_charts(self):
        if self._charts_frame is not None:
            self._charts_frame.destroy()
        self._bar_widget      = None
        self._line_widget     = None
        self._timeline_widget = None

        sf   = self._sf
        room = self._room_var.get() if hasattr(self, "_room_var") else "All Rooms"

        charts_frame = tk.Frame(sf, bg=WHITE)
        charts_frame.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 18))
        charts_frame.columnconfigure(0, weight=1)
        self._charts_frame = charts_frame

        # Top row: two side-by-side charts
        top_row = tk.Frame(charts_frame, bg=WHITE)
        top_row.grid(row=0, column=0, sticky="ew")
        top_row.columnconfigure(0, weight=1)
        top_row.columnconfigure(1, weight=1)

        self._bar_frame = tk.Frame(top_row, bg=WHITE, relief="groove", bd=1)
        self._bar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._line_frame = tk.Frame(top_row, bg=WHITE, relief="groove", bd=1)
        self._line_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._draw_bar_chart()
        self._draw_line_chart()

        # The Gantt timeline only makes sense when a single room is selected.
        if room != "All Rooms":
            self._timeline_frame = tk.Frame(charts_frame, bg=WHITE, relief="groove", bd=1)
            self._timeline_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
            self._draw_timeline_chart(room)

    def _build_stat_cards(self, cf):
        for i in range(4):
            cf.columnconfigure(i, weight=1, uniform="card")
        cf.rowconfigure(0, weight=1)

        uid = self._uid

        try:
            r = execute_query(
                "SELECT COUNT(*) as cnt FROM Violations WHERE user_id=%s AND status = 'active'",
                (uid,), fetch=True
            )
            violations = int(r[0]["cnt"]) if r else 0
        except Exception:
            violations = 0

        try:
            # Visits This Week uses the Monday-to-Sunday window of the current calendar week.
            r = execute_query(
                """SELECT COUNT(*) as cnt FROM Reservations
                   WHERE user_id=%s
                   AND status IN ('checked_in','completed')
                   AND reservation_date >= DATE(DATE_SUB(NOW(), INTERVAL WEEKDAY(NOW()) DAY))
                   AND reservation_date <= DATE(DATE_ADD(
                       DATE_SUB(NOW(), INTERVAL WEEKDAY(NOW()) DAY), INTERVAL 6 DAY))""",
                (uid,), fetch=True
            )
            visits = int(r[0]["cnt"]) if r else 0
        except Exception:
            visits = 0

        try:
            r = execute_query(
                "SELECT COALESCE(SUM(points_assessed), 0) as active_points"
                " FROM Violations WHERE user_id=%s AND status = 'active'",
                (uid,), fetch=True
            )
            pts = int(r[0]["active_points"] or 0) if r else 0
        except Exception:
            pts = 0

        try:
            r = execute_query(
                "SELECT account_status, suspended_until FROM Users WHERE user_id=%s",
                (uid,), fetch=True
            )
            if r:
                acct_status     = r[0]["account_status"]
                suspended_until = r[0].get("suspended_until")
            else:
                acct_status, suspended_until = "active", None
        except Exception:
            acct_status, suspended_until = "active", None

        self._make_card(cf, 0, str(violations), "My Violations",    GOLD,   MAROON)
        self._make_card(cf, 1, str(visits),      "Visits This Week", GOLD,   MAROON)

        # Penalty card colour escalates: green (safe) -> orange (warning) -> red (danger).
        if pts <= 4:
            c3_bg, c3_fg, c3_label = GREEN,  WHITE, "Penalty Points"
        elif pts <= 9:
            c3_bg, c3_fg, c3_label = ORANGE, WHITE, "Penalty Points - Warning"
        else:
            c3_bg, c3_fg, c3_label = RED,    WHITE, "Penalty Points - Danger"
        self._make_card(cf, 2, str(pts), c3_label, c3_bg, c3_fg)

        if acct_status == "suspended":
            c4_bg, c4_fg = RED,    WHITE
            c4_val        = "Suspended"
            c4_extra      = str(suspended_until)[:10] if suspended_until else ""
        elif pts >= 10:
            c4_bg, c4_fg = RED,    WHITE
            c4_val, c4_extra = "Suspended", ""
        elif pts >= 5:
            c4_bg, c4_fg = ORANGE, WHITE
            c4_val, c4_extra = "Caution", ""
        else:
            c4_bg, c4_fg = GREEN,  WHITE
            c4_val, c4_extra = "Good Standing", ""
        self._make_card(cf, 3, c4_val, "Account Standing", c4_bg, c4_fg,
                        extra=c4_extra, value_size=16)

    def _make_card(self, parent, col, value, label, bg, fg, extra="", value_size=28):
        card = tk.Frame(parent, bg=bg, padx=16, pady=16)
        card.configure(height=110)
        card.grid_propagate(False)
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        value_wrap = 130 if value_size < 28 else 120
        tk.Label(card, text=value, fg=fg, bg=bg,
                 font=("Poppins", value_size, "bold"),
                 wraplength=value_wrap, justify="center").pack(expand=True)
        tk.Label(card, text=label, fg=fg, bg=bg,
                 font=("Poppins", 11, "bold"),
                 wraplength=130, justify="center").pack()
        if extra:
            tk.Label(card, text=extra, fg=fg, bg=bg,
                     font=("Poppins", 9),
                     wraplength=130, justify="center").pack()

    def _build_filter_panel(self, ff):
        tk.Label(ff, text="Room:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 11)).grid(row=0, column=0, padx=(0, 4))
        self._room_var   = tk.StringVar(value="All Rooms")
        self._room_combo = ttk.Combobox(ff, textvariable=self._room_var,
                                        state="readonly", width=14, font=("Poppins", 11))
        self._room_combo.grid(row=0, column=1, padx=(0, 14))
        self._load_room_options()

        tk.Label(ff, text="Day:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 11)).grid(row=0, column=2, padx=(0, 4))
        self._day_var = tk.StringVar(value="All Days")
        ttk.Combobox(
            ff, textvariable=self._day_var, state="readonly", width=12,
            font=("Poppins", 11),
            values=["All Days", "Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday", "Sunday"]
        ).grid(row=0, column=3, padx=(0, 14))

        tk.Label(ff, text="Month:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 11)).grid(row=0, column=4, padx=(0, 4))
        self._month_var = tk.StringVar(value="All Months")
        ttk.Combobox(
            ff, textvariable=self._month_var, state="readonly", width=16,
            font=("Poppins", 11),
            values=["All Months", "January 2026", "February 2026",
                    "March 2026", "April 2026"]
        ).grid(row=0, column=5, padx=(0, 14))

        tk.Button(ff, text="Apply", fg=WHITE, bg=MAROON,
                  font=("Poppins", 11, "bold"), relief="flat", bd=0,
                  padx=14, pady=5, cursor="hand2",
                  command=self._apply_filters
                  ).grid(row=0, column=6, padx=(0, 6))

        tk.Button(ff, text="Reset", fg=BLACK, bg="#CCCCCC",
                  font=("Poppins", 11), relief="flat", bd=0,
                  padx=14, pady=5, cursor="hand2",
                  command=self._reset_filters
                  ).grid(row=0, column=7)

    def _load_room_options(self):
        try:
            rows = execute_query(
                "SELECT room_number FROM Rooms ORDER BY room_number", fetch=True
            )
            values = ["All Rooms"] + [r["room_number"] for r in rows]
        except Exception:
            values = ["All Rooms"]
        self._room_combo["values"] = values

    def _parse_month(self, month_str):
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        parts = month_str.split()
        return month_map[parts[0]], int(parts[1])

    def _apply_filters(self):
        self._rebuild_charts()

    def _reset_filters(self):
        self._room_var.set("All Rooms")
        self._day_var.set("All Days")
        self._month_var.set("All Months")
        self._rebuild_charts()

    # Shows all students' bookings per room so a student can see which rooms are most popular.
    def _draw_bar_chart(self):
        if self._bar_widget:
            self._bar_widget.get_tk_widget().destroy()
            self._bar_widget = None

        room  = self._room_var.get()  if hasattr(self, "_room_var")  else "All Rooms"
        day   = self._day_var.get()   if hasattr(self, "_day_var")   else "All Days"
        month = self._month_var.get() if hasattr(self, "_month_var") else "All Months"

        params = []
        extra  = ""
        if room != "All Rooms":
            extra += " AND r.room_number = %s"
            params.append(room)
        if day != "All Days":
            extra += " AND DAYNAME(res.reservation_date) = %s"
            params.append(day)
        if month != "All Months":
            month_num, year_num = self._parse_month(month)
            extra += " AND MONTH(res.reservation_date) = %s AND YEAR(res.reservation_date) = %s"
            params.extend([month_num, year_num])

        where_clause = (
            f"WHERE res.status IN ('reserved','checked_in','completed','no_show','cancelled'){extra}"
        )
        try:
            rows = execute_query(
                f"""SELECT r.room_number, COUNT(res.reservation_id) as bookings
                    FROM Reservations res
                    JOIN Rooms r ON r.room_id = res.room_id
                    {where_clause}
                    GROUP BY r.room_id, r.room_number
                    ORDER BY bookings DESC""",
                params if params else (), fetch=True
            )
        except Exception:
            rows = []

        fig = Figure(figsize=(5, 4), facecolor="white")
        ax  = fig.add_subplot(111)

        if rows:
            room_labels = [str(r["room_number"]) for r in rows]
            bookings    = [r["bookings"] for r in rows]
            x_pos = list(range(len(room_labels)))
            bars = ax.bar(x_pos, bookings, color=MAROON)
            for bar, val in zip(bars, bookings):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05,
                    str(int(val)), ha="center", va="bottom",
                    fontsize=8, fontweight="bold"
                )
            ax.set_xticks(x_pos)
            ax.set_xticklabels(room_labels, rotation=45, ha="right")
        else:
            ax.text(0.5, 0.5, "No data available",
                    ha="center", va="center", transform=ax.transAxes, fontsize=11)

        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_title("Most Booked Rooms (All Students)", fontsize=12, fontweight="bold", color=MAROON)
        ax.set_xlabel("Room Number",       fontsize=10)
        ax.set_ylabel("Number of Bookings", fontsize=10)
        ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
        ax.set_facecolor("#FAFAFA")
        fig.tight_layout(pad=1.5)

        fc = FigureCanvasTkAgg(fig, master=self._bar_frame)
        fc.draw()
        fc.get_tk_widget().pack(fill="both", expand=True)
        self._bar_widget = fc

    # Shows this student's own bookings grouped by weekday to reveal usage habits.
    def _draw_line_chart(self):
        if self._line_widget:
            self._line_widget.get_tk_widget().destroy()
            self._line_widget = None

        room  = self._room_var.get()  if hasattr(self, "_room_var")  else "All Rooms"
        month = self._month_var.get() if hasattr(self, "_month_var") else "All Months"

        params = [self._uid]
        extra  = ""
        if room != "All Rooms":
            extra += " AND room_id = (SELECT room_id FROM Rooms WHERE room_number=%s)"
            params.append(room)
        if month != "All Months":
            month_num, year_num = self._parse_month(month)
            extra += " AND MONTH(reservation_date) = %s AND YEAR(reservation_date) = %s"
            params.extend([month_num, year_num])

        try:
            rows = execute_query(
                f"""SELECT DAYNAME(reservation_date) as day_name,
                           DAYOFWEEK(reservation_date) as day_num,
                           COUNT(*) as total
                    FROM Reservations
                    WHERE user_id = %s
                    AND status IN ('completed', 'checked_in', 'reserved', 'no_show', 'cancelled')
                    {extra}
                    GROUP BY DAYNAME(reservation_date), DAYOFWEEK(reservation_date)
                    ORDER BY DAYOFWEEK(reservation_date)""",
                params, fetch=True
            )
        except Exception:
            rows = []

        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_short = ["Mon",    "Tue",      "Wed",       "Thu",      "Fri",    "Sat",      "Sun"]
        counts = {r["day_name"]: int(r["total"] or 0) for r in rows}
        values = [counts.get(day, 0) for day in days_order]

        fig = Figure(figsize=(5, 4), facecolor="white")
        ax  = fig.add_subplot(111)

        x_pos = list(range(7))
        bars = ax.bar(x_pos, values, color=MAROON)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                str(int(val)), ha="center", va="bottom",
                fontsize=8, fontweight="bold"
            )
        ax.set_xticks(x_pos)
        ax.set_xticklabels(days_short)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_title("Booking Pattern by Day of Week", fontsize=12, fontweight="bold", color=MAROON)
        ax.set_xlabel("Day of Week",       fontsize=10)
        ax.set_ylabel("Number of Bookings", fontsize=10)
        ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)
        ax.set_facecolor("#FAFAFA")
        fig.tight_layout(pad=1.5)

        fc = FigureCanvasTkAgg(fig, master=self._line_frame)
        fc.draw()
        fc.get_tk_widget().pack(fill="both", expand=True)
        self._line_widget = fc

    # Horizontal Gantt showing all bookings for the selected room so the student can see
    # what times are typically occupied before making a new reservation.
    def _draw_timeline_chart(self, room_number):
        if self._timeline_widget:
            self._timeline_widget.get_tk_widget().destroy()
            self._timeline_widget = None

        day   = self._day_var.get()   if hasattr(self, "_day_var")   else "All Days"
        month = self._month_var.get() if hasattr(self, "_month_var") else "All Months"

        params = [room_number]
        extra  = ""
        if day != "All Days":
            extra += " AND DAYNAME(res.reservation_date) = %s"
            params.append(day)
        if month != "All Months":
            month_num, year_num = self._parse_month(month)
            extra += " AND MONTH(res.reservation_date) = %s AND YEAR(res.reservation_date) = %s"
            params.extend([month_num, year_num])

        try:
            rows = execute_query(
                f"""SELECT res.reservation_date, res.start_time, res.end_time,
                           u.first_name, u.last_name, res.status
                    FROM Reservations res
                    JOIN Users u ON u.user_id = res.user_id
                    JOIN Rooms r ON r.room_id = res.room_id
                    WHERE r.room_number = %s
                    {extra}
                    AND res.status IN ('completed', 'checked_in', 'reserved', 'no_show', 'cancelled')
                    ORDER BY res.reservation_date ASC, res.start_time ASC""",
                params, fetch=True
            )
        except Exception:
            rows = []

        status_colors = {
            "completed":  "#5E1219",
            "checked_in": "#5E1219",
            "reserved":   "#3498db",
            "no_show":    "#e74c3c",
            "cancelled":  "#95a5a6",
        }

        fig = Figure(figsize=(7, max(3, len(rows) * 0.4)), facecolor="white")
        ax  = fig.add_subplot(111)

        if not rows:
            ax.text(0.5, 0.5, "No bookings found for this room",
                    ha="center", va="center", transform=ax.transAxes, fontsize=11)
        else:
            y_labels = []
            date_slot_counter: dict = {}
            for idx, row in enumerate(rows):
                rd = row["reservation_date"]
                dt = rd if hasattr(rd, "strftime") else datetime.strptime(str(rd), "%Y-%m-%d")
                date_str = dt.strftime("%b %d")
                date_slot_counter[date_str] = date_slot_counter.get(date_str, 0) + 1
                slot_num = date_slot_counter[date_str]
                y_labels.append(f"{date_str} - Slot {slot_num}")

                start_h = _time_to_hours(row["start_time"])
                end_h   = _time_to_hours(row["end_time"])
                width   = max(end_h - start_h, 0)
                color   = status_colors.get(row["status"], "#95a5a6")

                ax.barh(idx, width, left=start_h, height=0.6, color=color, align="center")

                if width >= 0.5:
                    t_s = f"{int(start_h):02d}:{int((start_h % 1) * 60):02d}"
                    t_e = f"{int(end_h):02d}:{int((end_h % 1) * 60):02d}"
                    ax.text(start_h + width / 2, idx, f"{t_s}-{t_e}",
                            ha="center", va="center", fontsize=7,
                            color="white", fontweight="bold")

            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels, fontsize=8)
            ax.set_xlim(8, 20)
            ax.set_xticks(range(8, 21))
            ax.set_xticklabels([f"{h:02d}:00" for h in range(8, 21)], fontsize=8)
            ax.set_xlabel("Time of Day", fontsize=10)
            ax.set_ylabel("Booking (Date - Student)", fontsize=10)

            legend_elements = [
                Patch(facecolor="#5E1219", label="Completed / Checked In"),
                Patch(facecolor="#3498db", label="Reserved"),
                Patch(facecolor="#e74c3c", label="No-Show"),
                Patch(facecolor="#95a5a6", label="Cancelled"),
            ]
            ax.legend(handles=legend_elements, fontsize=8, loc="lower right")

        ax.set_title(f"Booking Timeline - Room {room_number}",
                     fontsize=12, fontweight="bold", color=MAROON)
        ax.grid(axis="x", color="#EEEEEE", linewidth=0.8)
        ax.set_facecolor("#FAFAFA")
        fig.tight_layout(pad=1.5)

        fc = FigureCanvasTkAgg(fig, master=self._timeline_frame)
        fc.draw()
        fc.get_tk_widget().pack(fill="both", expand=True)
        self._timeline_widget = fc

    # Shows only the next 3 confirmed reservations so the widget stays compact.
    def _build_upcoming(self):
        uf = self._upcoming_frame
        for w in uf.winfo_children():
            w.destroy()

        tk.Label(uf, text="Upcoming Reservations",
                 fg=MAROON, bg=WHITE, font=("Poppins", 14, "bold")
                 ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        try:
            # Only 'reserved' status; checked_in and completed are already past their start time.
            rows = execute_query(
                """SELECT r.reservation_id, r.reservation_date, r.start_time,
                          r.end_time, r.status, ro.room_number, ro.room_name,
                          ro.room_category
                   FROM Reservations r
                   JOIN Rooms ro ON ro.room_id = r.room_id
                   WHERE r.user_id = %s
                   AND r.status = 'reserved'
                   ORDER BY r.reservation_date ASC, r.start_time ASC
                   LIMIT 3""",
                (self._uid,), fetch=True
            )
        except Exception:
            rows = []

        if not rows:
            tk.Label(uf, text="No upcoming reservations",
                     fg="#777777", bg=WHITE, font=("Poppins", 12)
                     ).grid(row=1, column=0, sticky="w")
            return

        col_defs = [
            ("Reservation ID", "reservation_id"),
            ("Room",           "room_number"),
            ("Category",       "room_category"),
            ("Date",           "reservation_date"),
            ("Start",          "start_time"),
            ("End",            "end_time"),
            ("Status",         "status"),
        ]

        table = tk.Frame(uf, bg=WHITE)
        table.grid(row=1, column=0, sticky="ew")
        for col_idx in range(len(col_defs)):
            table.columnconfigure(col_idx, weight=1)

        for col_idx, (col_label, _) in enumerate(col_defs):
            tk.Label(table, text=col_label,
                     fg=WHITE, bg=MAROON,
                     font=("Poppins", 10, "bold"),
                     padx=10, pady=7
                     ).grid(row=0, column=col_idx, sticky="ew", padx=1, pady=(0, 1))

        for row_idx, row in enumerate(rows, start=1):
            row_bg = WHITE if row_idx % 2 == 0 else LIGHT_GOLD
            values = [
                row["reservation_id"],
                row["room_number"],
                row["room_category"],
                str(row["reservation_date"])[:10],
                str(row["start_time"])[:5],
                str(row["end_time"])[:5],
                row["status"],
            ]
            for col_idx, val in enumerate(values):
                tk.Label(table, text=str(val),
                         fg=BLACK, bg=row_bg,
                         font=("Poppins", 10),
                         padx=10, pady=6
                         ).grid(row=row_idx, column=col_idx, sticky="ew", padx=1, pady=1)
