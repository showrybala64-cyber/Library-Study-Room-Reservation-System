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

COLS = ("Violation ID", "Reservation", "Room", "Type", "Points", "Status", "Date")


class ViolationsStudent(tk.Frame):
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
        content.rowconfigure(2, weight=1)
        content.rowconfigure(4, weight=0)

        tk.Label(content, text="My Violations",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w")

        # Filter / Sort bar
        ctrl_row = tk.Frame(content, bg=WHITE)
        ctrl_row.grid(row=1, column=0, sticky="w", pady=(10, 8))

        tk.Label(ctrl_row, text="Filter by status:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 6))
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(ctrl_row, textvariable=self.filter_var,
                     values=["All", "open", "resolved", "appealed"],
                     state="readonly", width=12,
                     font=("Poppins", 12)
                     ).pack(side="left", padx=(0, 10))

        tk.Button(ctrl_row, text="Filter",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._load_data
                  ).pack(side="left", padx=(0, 8))

        tk.Label(ctrl_row, text="Sort by:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(8, 6))
        self.sort_var = tk.StringVar(value="Date")
        ttk.Combobox(ctrl_row, textvariable=self.sort_var,
                     values=["Date", "Points", "Type"],
                     state="readonly", width=10,
                     font=("Poppins", 12)
                     ).pack(side="left", padx=(0, 8))
        tk.Button(ctrl_row, text="Sort",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._sort_data
                  ).pack(side="left")

        # Treeview
        tree_frame = tk.Frame(content, bg=WHITE)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        tree_border = tk.Frame(tree_frame,
                               highlightbackground=MAROON, highlightthickness=2)
        tree_border.grid(row=0, column=0, sticky="nsew")
        tree_border.columnconfigure(0, weight=1)
        tree_border.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_border, columns=COLS,
                                 show="headings", selectmode="browse",
                                 style="StudentVio.Treeview")
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("StudentVio.Treeview",
                    background="#FFFFFF", foreground="#000000", rowheight=30,
                    fieldbackground="#FFFFFF", bordercolor=MAROON,
                    borderwidth=2, font=("Poppins", 11))
        s.configure("StudentVio.Treeview.Heading",
                    background=MAROON, foreground="#FFFFFF",
                    font=("Poppins", 12, "bold"), borderwidth=2, relief="groove")
        s.map("StudentVio.Treeview",
              background=[("selected", MAROON)],
              foreground=[("selected", "#FFFFFF")])
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow",  background="#FFF8E7")
        for col in COLS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor="center")

        vsb = ttk.Scrollbar(tree_border, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_border, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Generate report section
        rpt_frame = tk.LabelFrame(content, text="Generate Report",
                                  bg=WHITE, fg=MAROON,
                                  font=("Poppins", 12, "bold"),
                                  padx=12, pady=8)
        rpt_frame.grid(row=3, column=0, sticky="ew", pady=(16, 0))

        tk.Label(rpt_frame, text="From:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 4))
        if _TKCAL:
            self.from_entry = DateEntry(
                rpt_frame, width=13,
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
                rpt_frame, textvariable=self.from_var, width=110,
                height=32, corner_radius=6,
                border_color=MAROON, border_width=1,
                fg_color=WHITE, text_color=BLACK, font=("Poppins", 12)
            )
        self.from_entry.pack(side="left", padx=(0, 12))

        tk.Label(rpt_frame, text="To:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 4))
        today = date.today()
        if _TKCAL:
            self.to_entry = DateEntry(
                rpt_frame, width=13,
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
                rpt_frame, textvariable=self.to_var, width=110,
                height=32, corner_radius=6,
                border_color=MAROON, border_width=1,
                fg_color=WHITE, text_color=BLACK, font=("Poppins", 12)
            )
        self.to_entry.pack(side="left", padx=(0, 12))

        tk.Button(rpt_frame, text="Generate",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
                  command=self._generate_report
                  ).pack(side="left")

        self._load_data()

    # ------------------------------------------------------------------
    def _load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            status_filter = self.filter_var.get()
            params = [self.user_info["user_id"]]
            extra  = ""
            if status_filter != "All":
                extra = " AND v.status = %s"
                params.append(status_filter)

            rows = execute_query(
                f"""SELECT v.violation_id, v.reservation_id, rm.room_number,
                           v.violation_type, v.points_assessed, v.status,
                           DATE(v.created_at) AS vdate
                    FROM Violations v
                    JOIN Reservations r  ON v.reservation_id = r.reservation_id
                    JOIN Rooms rm        ON r.room_id = rm.room_id
                    WHERE v.user_id = %s{extra}
                    ORDER BY v.created_at DESC""",
                params, fetch=True
            )
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=(
                    row["violation_id"], row["reservation_id"],
                    row["room_number"],  row["violation_type"],
                    row["points_assessed"], row["status"],
                    str(row["vdate"]),
                ), tags=(tag,))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _sort_data(self):
        sort_key = self.sort_var.get()
        col_map  = {"Date": 6, "Points": 4, "Type": 3}
        col_idx  = col_map.get(sort_key, 6)
        data     = [(self.tree.set(k, COLS[col_idx]), k)
                    for k in self.tree.get_children()]
        data.sort()
        for index, (_, k) in enumerate(data):
            self.tree.move(k, "", index)

    def _generate_report(self):
        if _TKCAL:
            from_date = self.from_entry.get_date().strftime("%Y-%m-%d")
            to_date   = self.to_entry.get_date().strftime("%Y-%m-%d")
        else:
            from_date = self.from_var.get().strip()
            to_date   = self.to_var.get().strip()
        try:
            rows = execute_query(
                """SELECT v.violation_id, v.violation_type, v.points_assessed,
                          v.status, DATE(v.created_at) AS vdate
                   FROM Violations v
                   WHERE v.user_id = %s
                     AND DATE(v.created_at) BETWEEN %s AND %s
                   ORDER BY v.created_at""",
                (self.user_info["user_id"], from_date, to_date), fetch=True
            )
            if not rows:
                messagebox.showinfo("Report", "No violations found in the selected date range.")
                return

            total_pts = sum(r["points_assessed"] or 0 for r in rows)
            lines = [f"Violations Report: {from_date} to {to_date}",
                     f"Total violations: {len(rows)}",
                     f"Total penalty points: {total_pts}",
                     "─" * 40]
            for r in rows:
                lines.append(
                    f"#{r['violation_id']}  {r['vdate']}  {r['violation_type']}  "
                    f"+{r['points_assessed']}pts  [{r['status']}]"
                )
            messagebox.showinfo("Violation Report", "\n".join(lines))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
