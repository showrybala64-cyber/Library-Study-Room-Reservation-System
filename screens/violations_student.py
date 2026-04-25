# Read-only violations view for students.
# Shows the student's own violation history with optional status and sort filters.

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from connect_db import execute_query

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"

COLS = ("Vio ID", "Room", "Type", "Points", "Status", "Date")

TYPE_MAP   = {"no_show": "No Show", "late_cancel": "Late Cancel"}
STATUS_MAP = {"active": "Open", "resolved": "Resolved"}


class ViolationsStudent(tk.Frame):
    def __init__(self, parent, user_info: dict, navigator, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.user_info = user_info
        self.navigator = navigator
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        content = tk.Frame(self, bg=WHITE)
        content.grid(row=0, column=0, sticky="nsew", padx=24, pady=16)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        tk.Label(content, text="My Violations",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w")

        # Filter / Sort bar
        ctrl_row = tk.Frame(content, bg=WHITE)
        ctrl_row.grid(row=1, column=0, sticky="w", pady=(10, 8))

        tk.Label(ctrl_row, text="Status:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 6))
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(ctrl_row, textvariable=self.filter_var,
                     values=["All", "Open", "Resolved"],
                     state="readonly", width=12,
                     font=("Poppins", 12)
                     ).pack(side="left", padx=(0, 14))

        tk.Label(ctrl_row, text="Sort by:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 6))
        self.sort_var = tk.StringVar(value="Date")
        ttk.Combobox(ctrl_row, textvariable=self.sort_var,
                     values=["Date", "Points"],
                     state="readonly", width=10,
                     font=("Poppins", 12)
                     ).pack(side="left", padx=(0, 14))

        tk.Button(ctrl_row, text="Apply",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
                  command=self._load_data
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
            self.tree.column(col, width=120, anchor="center")

        vsb = ttk.Scrollbar(tree_border, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_border, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._load_data()

    def _load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        status_filter = self.filter_var.get()
        sort_filter   = self.sort_var.get()

        query = (
            "SELECT v.violation_id, v.violation_type, v.points_assessed, "
            "v.status, v.notes, v.created_at, v.resolved_at, "
            "r.reservation_date, ro.room_number "
            "FROM Violations v "
            "JOIN Reservations r ON r.reservation_id = v.reservation_id "
            "JOIN Rooms ro ON ro.room_id = r.room_id "
            "WHERE v.user_id = %s"
        )
        params = [self.user_info["user_id"]]

        if status_filter == "Open":
            query += " AND v.status = 'active'"
        elif status_filter == "Resolved":
            query += " AND v.status = 'resolved'"

        if sort_filter == "Points":
            query += " ORDER BY v.points_assessed DESC"
        else:
            query += " ORDER BY v.created_at DESC"

        try:
            rows = execute_query(query, params, fetch=True)
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=(
                    row["violation_id"],
                    row["room_number"],
                    TYPE_MAP.get(row["violation_type"], row["violation_type"]),
                    row["points_assessed"],
                    STATUS_MAP.get(row["status"], row["status"]),
                    str(row["created_at"])[:10],
                ), tags=(tag,))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

