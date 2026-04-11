import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date
from connect_db import execute_query

try:
    from tkcalendar import DateEntry
    _TKCAL = True
except ImportError:
    _TKCAL = False

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"
LIGHT  = "#F9F9F9"

REPORT_TYPES = [
    "Room Usage Report",
    "Student Usage & Penalty Report",
    "Violations Report",
]


class Reports(tk.Frame):
    def __init__(self, parent, user_info: dict, navigator, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.user_info = user_info
        self.navigator = navigator
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        content = tk.Frame(self, bg=WHITE)
        content.grid(row=0, column=0, sticky="nsew", padx=24, pady=16)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(3, weight=1)

        tk.Label(content, text="Generate Reports",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w")

        # Controls
        ctrl = tk.Frame(content, bg=WHITE)
        ctrl.grid(row=1, column=0, sticky="ew", pady=(14, 8))

        tk.Label(ctrl, text="Report Type:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.rtype_var = tk.StringVar(value=REPORT_TYPES[0])
        ttk.Combobox(ctrl, textvariable=self.rtype_var,
                     values=REPORT_TYPES, state="readonly", width=34,
                     font=("Poppins", 12)
                     ).grid(row=0, column=1, sticky="w", padx=(0, 16))

        tk.Label(ctrl, text="Room Filter:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12, "bold")).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.room_var = tk.StringVar(value="All Rooms")
        self.room_combo = ttk.Combobox(ctrl, textvariable=self.room_var,
                                       state="readonly", width=18,
                                       font=("Poppins", 12))
        self.room_combo.grid(row=0, column=3, sticky="w", padx=(0, 16))
        self._load_rooms()

        tk.Label(ctrl, text="From:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).grid(row=1, column=0, sticky="w", pady=(8, 0))
        if _TKCAL:
            self.from_entry = DateEntry(
                ctrl, width=13,
                background=MAROON, foreground=WHITE, borderwidth=1,
                font=("Poppins", 12), date_pattern="yyyy-mm-dd",
                headersbackground=MAROON, headersforeground=WHITE,
                normalbackground=WHITE, normalforeground=BLACK,
                weekendbackground="#FFF0F0", weekendforeground=MAROON,
                selectbackground=MAROON, selectforeground=WHITE,
                year=2025, month=1, day=1,
            )
        else:
            self.from_var = tk.StringVar(value="2025-01-01")
            self.from_entry = ctk.CTkEntry(
                ctrl, textvariable=self.from_var, width=110,
                height=34, corner_radius=6,
                border_color=MAROON, border_width=1,
                fg_color=WHITE, text_color=BLACK, font=("Poppins", 12)
            )
        self.from_entry.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=(8, 0))

        tk.Label(ctrl, text="To:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).grid(row=1, column=2, sticky="w", pady=(8, 0))
        today = date.today()
        if _TKCAL:
            self.to_entry = DateEntry(
                ctrl, width=13,
                background=MAROON, foreground=WHITE, borderwidth=1,
                font=("Poppins", 12), date_pattern="yyyy-mm-dd",
                headersbackground=MAROON, headersforeground=WHITE,
                normalbackground=WHITE, normalforeground=BLACK,
                weekendbackground="#FFF0F0", weekendforeground=MAROON,
                selectbackground=MAROON, selectforeground=WHITE,
                year=today.year, month=today.month, day=today.day,
            )
        else:
            self.to_var = tk.StringVar(value="2026-12-31")
            self.to_entry = ctk.CTkEntry(
                ctrl, textvariable=self.to_var, width=110,
                height=34, corner_radius=6,
                border_color=MAROON, border_width=1,
                fg_color=WHITE, text_color=BLACK, font=("Poppins", 12)
            )
        self.to_entry.grid(row=1, column=3, sticky="w", padx=(0, 16), pady=(8, 0))

        tk.Button(ctrl, text="Generate Report",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 13, "bold"),
                  relief="flat", bd=0, padx=22, pady=9, cursor="hand2",
                  command=self._generate
                  ).grid(row=1, column=4, sticky="w", pady=(8, 0))

        # Separator
        ttk.Separator(content, orient="horizontal"
                      ).grid(row=2, column=0, sticky="ew", pady=(0, 8))

        # Results panel
        result_frame = tk.Frame(content, bg=LIGHT,
                                highlightbackground="#DDDDDD", highlightthickness=1)
        result_frame.grid(row=3, column=0, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.result_text = tk.Text(
            result_frame,
            bg=LIGHT, fg=BLACK,
            font=("Courier New", 12),
            wrap="word",
            relief="flat", bd=0,
            padx=16, pady=12,
            state="disabled"
        )
        vsb = ttk.Scrollbar(result_frame, orient="vertical",
                            command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=vsb.set)
        self.result_text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

    # ------------------------------------------------------------------
    def _load_rooms(self):
        try:
            rows = execute_query("SELECT room_number FROM Rooms ORDER BY room_number",
                                 fetch=True)
            values = ["All Rooms"] + [r["room_number"] for r in rows]
            self.room_combo["values"] = values
        except Exception:
            self.room_combo["values"] = ["All Rooms"]

    def _set_result(self, text):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", text)
        self.result_text.config(state="disabled")

    # ------------------------------------------------------------------
    def _generate(self):
        rtype     = self.rtype_var.get()
        room_filt = self.room_var.get()
        if _TKCAL:
            from_date = self.from_entry.get_date().strftime("%Y-%m-%d")
            to_date   = self.to_entry.get_date().strftime("%Y-%m-%d")
        else:
            from_date = self.from_var.get().strip()
            to_date   = self.to_var.get().strip()

        try:
            if rtype == "Room Usage Report":
                self._room_usage(room_filt, from_date, to_date)
            elif rtype == "Student Usage & Penalty Report":
                self._student_usage(from_date, to_date)
            elif rtype == "Violations Report":
                self._violations_report(room_filt, from_date, to_date)
        except Exception as exc:
            messagebox.showerror("Report Error", str(exc))

    # ------------------------------------------------------------------
    def _room_usage(self, room_filt, from_date, to_date):
        params = [from_date, to_date]
        extra  = ""
        if room_filt != "All Rooms":
            extra = " AND rm.room_number = %s"
            params.append(room_filt)

        rows = execute_query(
            f"""SELECT rm.room_number, rm.room_category,
                       COUNT(r.reservation_id) AS total_reservations,
                       SUM(CASE WHEN r.status = 'checked_in' THEN 1 ELSE 0 END) AS check_ins,
                       SUM(CASE WHEN r.status = 'cancelled'  THEN 1 ELSE 0 END) AS cancellations
                FROM Reservations r
                JOIN Rooms rm ON r.room_id = rm.room_id
                WHERE r.reservation_date BETWEEN %s AND %s{extra}
                GROUP BY rm.room_id, rm.room_number, rm.room_category
                ORDER BY total_reservations DESC""",
            params, fetch=True
        )
        if not rows:
            self._set_result("No data found for the selected range.")
            return

        lines = [
            f"ROOM USAGE REPORT  |  {from_date}  to  {to_date}",
            "=" * 70,
            f"{'Room':<12}{'Category':<20}{'Reservations':>14}"
            f"{'Check-Ins':>12}{'Cancellations':>16}",
            "-" * 70,
        ]
        for r in rows:
            lines.append(
                f"{r['room_number']:<12}{r['room_category']:<20}"
                f"{r['total_reservations']:>14}"
                f"{r['check_ins']:>12}"
                f"{r['cancellations']:>16}"
            )
        lines.append("=" * 70)
        self._set_result("\n".join(lines))

    def _student_usage(self, from_date, to_date):
        rows = execute_query(
            """SELECT u.user_id,
                      CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                      COUNT(r.reservation_id) AS reservations,
                      u.penalty_points,
                      u.account_status
               FROM Users u
               LEFT JOIN Reservations r
                  ON u.user_id = r.user_id
                  AND r.reservation_date BETWEEN %s AND %s
               WHERE u.role = 'student'
               GROUP BY u.user_id, student_name, u.penalty_points, u.account_status
               ORDER BY u.penalty_points DESC""",
            (from_date, to_date), fetch=True
        )
        if not rows:
            self._set_result("No student data found.")
            return

        lines = [
            f"STUDENT USAGE & PENALTY REPORT  |  {from_date}  to  {to_date}",
            "=" * 72,
            f"{'User ID':<10}{'Name':<28}{'Reservations':>14}"
            f"{'Penalty Pts':>13}{'Status':>12}",
            "-" * 72,
        ]
        for r in rows:
            lines.append(
                f"{r['user_id']:<10}{r['student_name']:<28}"
                f"{r['reservations']:>14}"
                f"{r['points_assessed']:>13}"
                f"{r['account_status']:>12}"
            )
        lines.append("=" * 72)
        self._set_result("\n".join(lines))

    def _violations_report(self, room_filt, from_date, to_date):
        params = [from_date, to_date]
        extra  = ""
        if room_filt != "All Rooms":
            extra = " AND rm.room_number = %s"
            params.append(room_filt)

        rows = execute_query(
            f"""SELECT v.violation_id,
                       CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                       rm.room_number, v.violation_type,
                       v.points_assessed, v.status,
                       DATE(v.created_at) AS vdate
                FROM Violations v
                JOIN Users u        ON v.user_id = u.user_id
                JOIN Reservations r ON v.reservation_id = r.reservation_id
                JOIN Rooms rm       ON r.room_id = rm.room_id
                WHERE DATE(v.created_at) BETWEEN %s AND %s{extra}
                ORDER BY v.created_at DESC""",
            params, fetch=True
        )
        if not rows:
            self._set_result("No violations found for the selected range.")
            return

        total_pts = sum(r["points_assessed"] or 0 for r in rows)
        lines = [
            f"VIOLATIONS REPORT  |  {from_date}  to  {to_date}",
            "=" * 74,
            f"{'ID':<6}{'Student':<26}{'Room':<10}{'Type':<18}"
            f"{'Pts':>5}{'Status':>10}{'Date':>12}",
            "-" * 74,
        ]
        for r in rows:
            lines.append(
                f"{r['violation_id']:<6}{r['student_name']:<26}"
                f"{r['room_number']:<10}{r['violation_type']:<18}"
                f"{r['points_assessed']:>5}{r['status']:>10}"
                f"{str(r['vdate']):>12}"
            )
        lines += [
            "=" * 74,
            f"Total violations: {len(rows)}   Total penalty points issued: {total_pts}",
        ]
        self._set_result("\n".join(lines))
