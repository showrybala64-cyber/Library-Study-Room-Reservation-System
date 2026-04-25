# Admin violations browser with date-range filtering and inline status/notes editing.
# Admin can resolve a violation or add notes; resolved_at is set automatically on resolve.

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date
from connect_db import execute_query

from components.date_picker import make_date_entry

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
        self.from_entry = make_date_entry(filter_row, default_date="2025-01-01")
        self.from_entry.pack(side="left", padx=(0, 12))

        tk.Label(filter_row, text="To:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(side="left", padx=(0, 4))
        today = date.today()
        self.to_entry = make_date_entry(filter_row, default_date=today.strftime("%Y-%m-%d"))
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
                  ).pack(side="left", padx=(0, 8))

        tk.Button(filter_row, text="Edit Violation",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
                  command=self._edit_violation
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

    # Opens inline editor for status and notes; sets resolved_at when status changes to resolved.
    def _edit_violation(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Edit Violation", "Please select a violation to edit.")
            return

        vals    = self.tree.item(sel[0])["values"]
        vio_id  = vals[0]
        student = vals[2]
        room    = vals[3]
        vtype   = vals[4]
        points  = vals[5]
        status  = vals[6]
        vdate   = vals[7]

        # Fetch current notes from DB
        try:
            rows = execute_query(
                "SELECT notes FROM Violations WHERE violation_id = %s",
                (vio_id,), fetch=True
            )
            current_notes = rows[0]["notes"] if rows and rows[0]["notes"] else ""
        except Exception:
            current_notes = ""

        win = tk.Toplevel(self)
        win.title(f"Edit Violation #{vio_id}")
        win.geometry("400x500")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.grab_set()
        self.update_idletasks()
        wx = self.winfo_rootx() + (self.winfo_width()  - 400) // 2
        wy = self.winfo_rooty() + (self.winfo_height() - 500) // 2
        win.geometry(f"400x500+{wx}+{wy}")

        # Scrollable canvas layout
        canvas = tk.Canvas(win, bg=WHITE, highlightthickness=0)
        vsb    = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        sf = tk.Frame(canvas, bg=WHITE)
        win_id = canvas.create_window((0, 0), window=sf, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        sf.bind("<Configure>", _on_configure)

        def _on_canvas_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        def _on_mousewheel(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass
        win.bind("<MouseWheel>",    _on_mousewheel)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        sf.bind("<MouseWheel>",     _on_mousewheel)

        # Header inside scrollable frame
        tk.Label(sf, text=f"Edit Violation #{vio_id}", fg=MAROON, bg=WHITE,
                 font=("Poppins", 16, "bold")).pack(pady=(16, 4), padx=24, anchor="w")
        tk.Frame(sf, bg="#E0E0E0", height=1).pack(fill="x", padx=20, pady=(0, 10))

        form = tk.Frame(sf, bg=WHITE)
        form.pack(fill="x", padx=24)

        def _ro_row(label, value):
            tk.Label(form, text=label, fg="#555555", bg=WHITE,
                     font=("Poppins", 10, "bold"), anchor="w").pack(fill="x", pady=(6, 0))
            tk.Label(form, text=str(value), fg=BLACK, bg="#F5F5F5",
                     font=("Poppins", 11), anchor="w", relief="flat",
                     padx=8, pady=4).pack(fill="x")
            tk.Label(form, bg=WHITE).bind("<MouseWheel>", _on_mousewheel)

        _ro_row("Violation ID",  vio_id)
        _ro_row("Student Name",  student)
        _ro_row("Room",          room)
        _ro_row("Type",          vtype)
        _ro_row("Points",        points)
        _ro_row("Date",          vdate)

        tk.Label(form, text="Status", fg="#555555", bg=WHITE,
                 font=("Poppins", 10, "bold"), anchor="w").pack(fill="x", pady=(10, 0))
        st_var = tk.StringVar(value=str(status))
        ttk.Combobox(form, textvariable=st_var, values=["active", "resolved"],
                     state="readonly", font=("Poppins", 11)
                     ).pack(fill="x", pady=(2, 0))

        tk.Label(form, text="Notes", fg="#555555", bg=WHITE,
                 font=("Poppins", 10, "bold"), anchor="w").pack(fill="x", pady=(10, 0))
        notes_box = tk.Text(form, height=4, font=("Poppins", 11),
                            bg=WHITE, fg=BLACK, relief="solid",
                            bd=1, wrap="word")
        notes_box.pack(fill="x", pady=(2, 0))
        notes_box.insert("1.0", current_notes)

        def _save():
            new_status = st_var.get()
            new_notes  = notes_box.get("1.0", "end-1c").strip()
            try:
                execute_query(
                    """UPDATE Violations
                       SET status=%s, notes=%s,
                           resolved_at=CASE WHEN %s='resolved' THEN NOW() ELSE NULL END
                       WHERE violation_id=%s""",
                    (new_status, new_notes, new_status, vio_id)
                )
                win.destroy()
                messagebox.showinfo("Edit Violation", f"Violation #{vio_id} updated successfully.")
                self._fetch(None, None)
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=win)

        # Buttons inside scrollable frame, below the form
        tk.Frame(sf, bg="#E0E0E0", height=1).pack(fill="x", padx=20, pady=(16, 0))
        btn_row = tk.Frame(sf, bg=WHITE)
        btn_row.pack(pady=(10, 20))
        tk.Button(btn_row, text="Cancel",
                  fg="#555555", bg="#E0E0E0",
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=win.destroy).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="Save Changes",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=_save).pack(side="left")

        def _bind_scroll(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_scroll(child)
        _bind_scroll(sf)

    def _load_all(self):
        self._fetch(None, None)

    def _load_data(self):
        from_date = self.from_entry.get().strip()
        to_date   = self.to_entry.get().strip()
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
