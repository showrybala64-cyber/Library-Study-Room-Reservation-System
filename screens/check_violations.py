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

COLS = ("Vio ID", "Student ID", "Student Name", "Room", "Type",
        "Points", "Status", "Date")


class CheckViolations(tk.Frame):
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

        tk.Label(content, text="All Student Violations",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w")

        # Date filter bar
        filter_row = tk.Frame(content, bg=WHITE)
        filter_row.grid(row=1, column=0, sticky="w", pady=(12, 8))

        tk.Label(filter_row, text="From:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 4))
        if _TKCAL:
            self.from_entry = DateEntry(
                filter_row, width=13,
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
                filter_row, textvariable=self.from_var, width=110,
                height=34, corner_radius=6,
                border_color=MAROON, border_width=1,
                fg_color=WHITE, text_color=BLACK, font=("Poppins", 12)
            )
        self.from_entry.pack(side="left", padx=(0, 12))

        tk.Label(filter_row, text="To:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 4))
        today = date.today()
        if _TKCAL:
            self.to_entry = DateEntry(
                filter_row, width=13,
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
                filter_row, textvariable=self.to_var, width=110,
                height=34, corner_radius=6,
                border_color=MAROON, border_width=1,
                fg_color=WHITE, text_color=BLACK, font=("Poppins", 12)
            )
        self.to_entry.pack(side="left", padx=(0, 12))

        tk.Button(filter_row, text="Generate",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
                  command=self._load_data
                  ).pack(side="left", padx=(0, 8))

        tk.Button(filter_row, text="Show All",
                  fg=MAROON, bg=GOLD,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
                  command=self._load_all
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
                                 style="AdminVio.Treeview")
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("AdminVio.Treeview",
                    background="#FFFFFF", foreground="#000000", rowheight=30,
                    fieldbackground="#FFFFFF", bordercolor=MAROON,
                    borderwidth=2, font=("Poppins", 11))
        s.configure("AdminVio.Treeview.Heading",
                    background=MAROON, foreground="#FFFFFF",
                    font=("Poppins", 12, "bold"), borderwidth=2, relief="groove")
        s.map("AdminVio.Treeview",
              background=[("selected", MAROON)],
              foreground=[("selected", "#FFFFFF")])
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow",  background="#FFF8E7")
        for col in COLS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        vsb = ttk.Scrollbar(tree_border, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_border, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._load_all()

    # ------------------------------------------------------------------
    def _load_all(self):
        self._fetch(None, None)

    def _load_data(self):
        if _TKCAL:
            from_date = self.from_entry.get_date().strftime("%Y-%m-%d")
            to_date   = self.to_entry.get_date().strftime("%Y-%m-%d")
        else:
            from_date = self.from_var.get().strip()
            to_date   = self.to_var.get().strip()
        self._fetch(from_date, to_date)

    def _fetch(self, from_date, to_date):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            if from_date and to_date:
                rows = execute_query(
                    """SELECT v.violation_id, v.user_id,
                              CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                              rm.room_number, v.violation_type,
                              v.points_assessed, v.status,
                              DATE(v.created_at)
                       FROM Violations v
                       JOIN Users u         ON v.user_id = u.user_id
                       JOIN Reservations r  ON v.reservation_id = r.reservation_id
                       JOIN Rooms rm        ON r.room_id = rm.room_id
                       WHERE DATE(v.created_at) BETWEEN %s AND %s
                       ORDER BY v.created_at DESC""",
                    (from_date, to_date), fetch=True
                )
            else:
                rows = execute_query(
                    """SELECT v.violation_id, v.user_id,
                              CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                              rm.room_number, v.violation_type,
                              v.points_assessed, v.status,
                              DATE(v.created_at)
                       FROM Violations v
                       JOIN Users u         ON v.user_id = u.user_id
                       JOIN Reservations r  ON v.reservation_id = r.reservation_id
                       JOIN Rooms rm        ON r.room_id = rm.room_id
                       ORDER BY v.created_at DESC""",
                    fetch=True
                )
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=list(row.values()), tags=(tag,))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
