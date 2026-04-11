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
LIGHT  = "#F5F5F5"

RULE_COLS = ("ID", "Effective From", "Max(min)", "Grace(min)",
             "Cancel(min)", "No-Show Pts", "Late Cancel Pts", "Active")
VIO_COLS  = ("Vio ID", "Student ID", "Room", "Type", "Pts", "Status", "Date")


class ManageRulesViolations(tk.Frame):
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
        content.rowconfigure(4, weight=1)
        content.rowconfigure(7, weight=1)

        tk.Label(content, text="Manage Rules & Violations",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        # Stats
        stats_frame = tk.Frame(content, bg=WHITE)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        stats_center = tk.Frame(stats_frame, bg=WHITE)
        stats_center.pack(pady=8)
        self._stat_lbls = {}
        for key in ["Total Rules", "Total Violations", "Active Violations"]:
            card = ctk.CTkFrame(stats_center, width=160, height=85,
                                fg_color=GOLD,
                                border_color=MAROON, border_width=2,
                                corner_radius=10)
            card.pack(side="left", padx=12)
            card.pack_propagate(False)
            tk.Label(card, text=key, fg=MAROON, bg=GOLD,
                     font=("Poppins", 13, "bold")).pack(pady=(12, 0))
            lbl = tk.Label(card, text="–", fg=MAROON, bg=GOLD,
                           font=("Poppins", 28, "bold"))
            lbl.pack()
            self._stat_lbls[key] = lbl

        # ── Rules Section ─────────────────────────────────────────────
        tk.Label(content, text="Library Rule Sets",
                 fg=MAROON, bg=WHITE, font=("Poppins", 15, "bold")
                 ).grid(row=2, column=0, sticky="w", pady=(0, 4))

        rule_btn_row = tk.Frame(content, bg=WHITE)
        rule_btn_row.grid(row=3, column=0, sticky="w", pady=(0, 6))
        for lbl, cmd in [("Add Rule Set", self._add_rule),
                          ("Edit Rule Set", self._edit_rule),
                          ("Remove Rule Set", self._remove_rule),
                          ("Refresh", self._load_data)]:
            tk.Button(rule_btn_row, text=lbl,
                      fg=WHITE, bg=MAROON if "Remove" not in lbl else "#AA0000",
                      font=("Poppins", 12, "bold"),
                      relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                      command=cmd
                      ).pack(side="left", padx=(0, 8))

        rule_frame = tk.Frame(content, bg=WHITE)
        rule_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 12))
        rule_frame.columnconfigure(0, weight=1)
        rule_frame.rowconfigure(0, weight=1)

        rule_border = tk.Frame(rule_frame,
                               highlightbackground=MAROON, highlightthickness=2)
        rule_border.grid(row=0, column=0, sticky="nsew")
        rule_border.columnconfigure(0, weight=1)
        rule_border.rowconfigure(0, weight=1)

        self.rule_tree = ttk.Treeview(rule_border, columns=RULE_COLS,
                                      show="headings", selectmode="browse", height=5,
                                      style="Rules.Treeview")
        _s = ttk.Style()
        _s.theme_use("clam")
        _s.configure("Rules.Treeview",
                     background="#FFFFFF", foreground="#000000", rowheight=30,
                     fieldbackground="#FFFFFF", bordercolor=MAROON,
                     borderwidth=2, font=("Poppins", 11))
        _s.configure("Rules.Treeview.Heading",
                     background=MAROON, foreground="#FFFFFF",
                     font=("Poppins", 12, "bold"), borderwidth=2, relief="groove")
        _s.map("Rules.Treeview",
               background=[("selected", MAROON)],
               foreground=[("selected", "#FFFFFF")])
        self.rule_tree.tag_configure("evenrow", background="#FFFFFF")
        self.rule_tree.tag_configure("oddrow",  background="#FFF8E7")
        col_widths = [40, 110, 80, 80, 80, 90, 110, 50]
        for col, w in zip(RULE_COLS, col_widths):
            self.rule_tree.heading(col, text=col)
            self.rule_tree.column(col, width=w, anchor="center")

        vsb1 = ttk.Scrollbar(rule_border, orient="vertical", command=self.rule_tree.yview)
        hsb1 = ttk.Scrollbar(rule_border, orient="horizontal", command=self.rule_tree.xview)
        self.rule_tree.configure(yscrollcommand=vsb1.set, xscrollcommand=hsb1.set)
        self.rule_tree.grid(row=0, column=0, sticky="nsew")
        vsb1.grid(row=0, column=1, sticky="ns")
        hsb1.grid(row=1, column=0, sticky="ew")

        # ── Violations Section ────────────────────────────────────────
        tk.Label(content, text="Violation Records",
                 fg=MAROON, bg=WHITE, font=("Poppins", 15, "bold")
                 ).grid(row=5, column=0, sticky="w", pady=(0, 4))

        vio_btn_row = tk.Frame(content, bg=WHITE)
        vio_btn_row.grid(row=6, column=0, sticky="w", pady=(0, 6))
        tk.Button(vio_btn_row, text="Edit Violation",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._edit_violation
                  ).pack(side="left")

        vio_frame = tk.Frame(content, bg=WHITE)
        vio_frame.grid(row=7, column=0, sticky="nsew")
        vio_frame.columnconfigure(0, weight=1)
        vio_frame.rowconfigure(0, weight=1)

        vio_border = tk.Frame(vio_frame,
                              highlightbackground=MAROON, highlightthickness=2)
        vio_border.grid(row=0, column=0, sticky="nsew")
        vio_border.columnconfigure(0, weight=1)
        vio_border.rowconfigure(0, weight=1)

        self.vio_tree = ttk.Treeview(vio_border, columns=VIO_COLS,
                                     show="headings", selectmode="browse", height=6,
                                     style="Rules.Treeview")
        self.vio_tree.tag_configure("evenrow", background="#FFFFFF")
        self.vio_tree.tag_configure("oddrow",  background="#FFF8E7")
        for col in VIO_COLS:
            self.vio_tree.heading(col, text=col)
            self.vio_tree.column(col, width=110, anchor="center")
        vsb2 = ttk.Scrollbar(vio_border, orient="vertical", command=self.vio_tree.yview)
        hsb2 = ttk.Scrollbar(vio_border, orient="horizontal", command=self.vio_tree.xview)
        self.vio_tree.configure(yscrollcommand=vsb2.set, xscrollcommand=hsb2.set)
        self.vio_tree.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        hsb2.grid(row=1, column=0, sticky="ew")

        self._load_data()

    # ------------------------------------------------------------------
    def _load_data(self):
        for r in self.rule_tree.get_children():
            self.rule_tree.delete(r)
        for r in self.vio_tree.get_children():
            self.vio_tree.delete(r)

        try:
            rules = execute_query(
                """SELECT rule_set_id, effective_from, max_booking_minutes,
                          checkin_grace_minutes, cancel_cutoff_minutes,
                          points_no_show, points_late_cancel, is_active
                   FROM Rules ORDER BY rule_set_id""",
                fetch=True
            )
            for i, r in enumerate(rules):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.rule_tree.insert("", "end", values=(
                    r["rule_set_id"],
                    str(r["effective_from"] or ""),
                    r["max_booking_minutes"],
                    r["checkin_grace_minutes"],
                    r["cancel_cutoff_minutes"],
                    r["points_no_show"],
                    r["points_late_cancel"],
                    "Yes" if r["is_active"] else "No",
                ), tags=(tag,))

            vios = execute_query(
                """SELECT v.violation_id, v.user_id, rm.room_number,
                          v.violation_type, v.points_assessed, v.status,
                          DATE(v.created_at)
                   FROM Violations v
                   JOIN Reservations res ON v.reservation_id = res.reservation_id
                   JOIN Rooms rm         ON res.room_id = rm.room_id
                   ORDER BY v.created_at DESC""",
                fetch=True
            )
            for i, r in enumerate(vios):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.vio_tree.insert("", "end", values=list(r.values()), tags=(tag,))

            self._stat_lbls["Total Rules"].config(text=str(len(rules)))
            self._stat_lbls["Total Violations"].config(text=str(len(vios)))
            active_v = sum(1 for r in vios if r["status"] == "open")
            self._stat_lbls["Active Violations"].config(text=str(active_v))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    # ------------------------------------------------------------------
    def _add_rule(self):
        win = tk.Toplevel(self)
        win.title("Add Rule Set")
        win.geometry("620x600")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.grab_set()
        self.update_idletasks()
        wx = self.winfo_rootx() + (self.winfo_width()  - 620) // 2
        wy = self.winfo_rooty() + (self.winfo_height() - 600) // 2
        win.geometry(f"620x600+{wx}+{wy}")

        # ── Header ─────────────────────────────────────────────────────
        tk.Label(win, text="Add Library Rule Set", fg=MAROON, bg=WHITE,
                 font=("Poppins", 16, "bold")).pack(pady=(18, 6))
        tk.Frame(win, bg="#E0E0E0", height=1).pack(fill="x", padx=24)

        # ── Footer (packed before body so it stays anchored) ───────────
        footer = tk.Frame(win, bg=WHITE)
        footer.pack(side="bottom", fill="x", pady=(0, 14))
        tk.Frame(footer, bg="#E0E0E0", height=1).pack(fill="x", padx=24, pady=(0, 10))
        btn_row = tk.Frame(footer, bg=WHITE)
        btn_row.pack()

        # ── Scrollable form body ────────────────────────────────────────
        wrap = tk.Frame(win, bg=WHITE)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)

        canvas = tk.Canvas(wrap, bg=WHITE, highlightthickness=0)
        vsb    = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        form = tk.Frame(canvas, bg=WHITE)
        fid  = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>",   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(fid, width=e.width))

        def _wh(e): canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _wh)
        form.bind("<MouseWheel>",   _wh)

        HINT_COLOR = "#777777"

        def _row(label, hint, widget_factory):
            """Add a label+hint row then call widget_factory(form) to build the input."""
            row_f = tk.Frame(form, bg=WHITE)
            row_f.pack(fill="x", padx=24, pady=(10, 0))
            row_f.bind("<MouseWheel>", _wh)
            tk.Label(row_f, text=label, fg=BLACK, bg=WHITE,
                     font=("Poppins", 11, "bold"), anchor="w"
                     ).pack(side="left")
            tk.Label(row_f, text=f"  {hint}", fg=HINT_COLOR, bg=WHITE,
                     font=("Poppins", 10), anchor="w"
                     ).pack(side="left")
            w = widget_factory(form)
            w.bind("<MouseWheel>", _wh)
            return w

        # ── Effective From ──────────────────────────────────────────────
        eff_var = tk.StringVar(value=str(date.today()))
        row_f0 = tk.Frame(form, bg=WHITE)
        row_f0.pack(fill="x", padx=24, pady=(10, 0))
        row_f0.bind("<MouseWheel>", _wh)
        tk.Label(row_f0, text="Effective From", fg=BLACK, bg=WHITE,
                 font=("Poppins", 11, "bold"), anchor="w").pack(side="left")
        tk.Label(row_f0, text="  Date this rule set takes effect",
                 fg=HINT_COLOR, bg=WHITE, font=("Poppins", 10)).pack(side="left")

        if _TKCAL:
            eff_widget = DateEntry(form, textvariable=eff_var, date_pattern="yyyy-mm-dd",
                                   width=14, background=MAROON, foreground=WHITE,
                                   borderwidth=1, font=("Poppins", 11))
        else:
            eff_widget = ctk.CTkEntry(form, textvariable=eff_var, height=34,
                                      corner_radius=6, border_color=MAROON,
                                      border_width=1, fg_color=WHITE,
                                      text_color=BLACK, font=("Poppins", 11))
        eff_widget.pack(fill="x", padx=24, pady=(2, 0))
        eff_widget.bind("<MouseWheel>", _wh)

        # ── Numeric fields ──────────────────────────────────────────────
        FIELDS = [
            ("Max Booking (minutes) *",       "max_book",    "120",
             "Max minutes a room can be reserved per booking"),
            ("Check-in Grace (minutes) *",    "grace",       "15",
             "Minutes after start time before marking as no-show"),
            ("Cooldown (minutes)",            "cooldown",    "30",
             "Required wait between bookings by the same student"),
            ("Cancel Cutoff (minutes) *",     "cutoff",      "60",
             "Minutes before start time — cancellations after this incur points"),
            ("Points: No Show *",             "pts_no_show", "3",
             "Penalty points for missing a reservation"),
            ("Points: Late Cancel *",         "pts_late",    "2",
             "Penalty points for cancelling after the cutoff"),
            ("Suspension Threshold (pts) *",  "susp_thresh", "10",
             "Total points that trigger an account suspension"),
            ("Suspension Duration (days) *",  "susp_days",   "7",
             "How many days an account stays suspended"),
        ]
        vars_ = {}
        for label, key, default, hint in FIELDS:
            row_frame = tk.Frame(form, bg=WHITE)
            row_frame.pack(fill="x", padx=24, pady=(10, 0))
            row_frame.bind("<MouseWheel>", _wh)
            tk.Label(row_frame, text=label, fg=BLACK, bg=WHITE,
                     font=("Poppins", 11, "bold"), anchor="w").pack(side="left")
            tk.Label(row_frame, text=f"  {hint}", fg=HINT_COLOR, bg=WHITE,
                     font=("Poppins", 10)).pack(side="left")
            var = tk.StringVar(value=default)
            vars_[key] = var
            entry = ctk.CTkEntry(form, textvariable=var, height=34, corner_radius=6,
                                 border_color=MAROON, border_width=1,
                                 fg_color=WHITE, text_color=BLACK,
                                 font=("Poppins", 11))
            entry.pack(fill="x", padx=24, pady=(2, 0))
            entry.bind("<MouseWheel>", _wh)

        # ── is_active checkbox ──────────────────────────────────────────
        active_var = tk.BooleanVar(value=True)
        chk_frame = tk.Frame(form, bg=WHITE)
        chk_frame.pack(fill="x", padx=24, pady=(14, 0))
        chk_frame.bind("<MouseWheel>", _wh)
        ctk.CTkCheckBox(chk_frame, text="Set as Active Rule Set",
                        variable=active_var,
                        fg_color=MAROON, hover_color="#7A1820",
                        checkmark_color=WHITE, border_color=MAROON,
                        font=("Poppins", 12, "bold"), text_color=BLACK
                        ).pack(side="left")
        tk.Label(chk_frame, text="  (disables all other rule sets)",
                 fg=HINT_COLOR, bg=WHITE, font=("Poppins", 10)).pack(side="left")
        tk.Frame(form, bg=WHITE, height=16).pack()

        # ── Submit logic ────────────────────────────────────────────────
        def _submit():
            try:
                eff_date  = eff_var.get().strip() or str(date.today())
                max_book  = int(vars_["max_book"].get())
                grace     = int(vars_["grace"].get())
                cooldown  = int(vars_["cooldown"].get() or 0)
                cutoff    = int(vars_["cutoff"].get())
                pts_ns    = int(vars_["pts_no_show"].get())
                pts_lc    = int(vars_["pts_late"].get())
                susp_thr  = int(vars_["susp_thresh"].get())
                susp_days = int(vars_["susp_days"].get())
            except ValueError:
                messagebox.showwarning("Add Rule Set",
                                       "All numeric fields must be integers.", parent=win)
                return

            try:
                if active_var.get():
                    execute_query("UPDATE Rules SET is_active = FALSE")
                execute_query(
                    """INSERT INTO Rules (effective_from, max_booking_minutes,
                                         checkin_grace_minutes, cooldown_minutes,
                                         cancel_cutoff_minutes, points_no_show,
                                         points_late_cancel, suspension_threshold_points,
                                         suspension_duration_days, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (eff_date, max_book, grace, cooldown, cutoff,
                     pts_ns, pts_lc, susp_thr, susp_days,
                     active_var.get())
                )
                messagebox.showinfo("Add Rule Set", "Rule set saved successfully.", parent=win)
                win.destroy()
                self._load_data()
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=win)

        # ── Footer buttons ──────────────────────────────────────────────
        tk.Button(btn_row, text="Cancel",
                  fg="#555555", bg="#E0E0E0",
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=win.destroy).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="Save Rule Set",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=_submit).pack(side="left")

    # ------------------------------------------------------------------
    def _edit_rule(self):
        sel = self.rule_tree.selection()
        if not sel:
            messagebox.showwarning("Edit", "Select a rule set first.")
            return
        rule_set_id = self.rule_tree.item(sel[0])["values"][0]

        try:
            rows = execute_query(
                "SELECT * FROM Rules WHERE rule_set_id = %s",
                (rule_set_id,), fetch=True
            )
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return
        if not rows:
            return
        r = rows[0]

        win = tk.Toplevel(self)
        win.title(f"Edit Rule Set #{rule_set_id}")
        win.geometry("420x400")
        win.configure(bg=WHITE)
        win.grab_set()

        tk.Label(win, text=f"Edit Rule Set #{rule_set_id}", fg=MAROON, bg=WHITE,
                 font=("Poppins", 16, "bold")).pack(pady=(16, 10))

        edit_fields = [
            ("Max Booking (minutes)",        "max_booking_minutes",         r["max_booking_minutes"]),
            ("Check-in Grace (minutes)",     "checkin_grace_minutes",       r["checkin_grace_minutes"]),
            ("Cooldown (minutes)",           "cooldown_minutes",            r["cooldown_minutes"]),
            ("Cancel Cutoff (minutes)",      "cancel_cutoff_minutes",       r["cancel_cutoff_minutes"]),
            ("Points: No Show",              "points_no_show",              r["points_no_show"]),
            ("Points: Late Cancel",          "points_late_cancel",          r["points_late_cancel"]),
            ("Suspension Threshold (pts)",   "suspension_threshold_points", r["suspension_threshold_points"]),
            ("Suspension Duration (days)",   "suspension_duration_days",    r["suspension_duration_days"]),
        ]
        vars_ = {}
        for label, key, val in edit_fields:
            tk.Label(win, text=label, fg=BLACK, bg=WHITE,
                     font=("Poppins", 11)).pack(anchor="w", padx=30)
            var = tk.StringVar(value=str(val or ""))
            vars_[key] = var
            ctk.CTkEntry(win, textvariable=var, height=32, corner_radius=6,
                         border_color=MAROON, border_width=1,
                         fg_color=WHITE, text_color=BLACK,
                         font=("Poppins", 11)
                         ).pack(fill="x", padx=30, pady=(2, 6))

        def save():
            try:
                execute_query(
                    """UPDATE Rules SET
                           max_booking_minutes        = %s,
                           checkin_grace_minutes      = %s,
                           cooldown_minutes           = %s,
                           cancel_cutoff_minutes      = %s,
                           points_no_show             = %s,
                           points_late_cancel         = %s,
                           suspension_threshold_points= %s,
                           suspension_duration_days   = %s
                       WHERE rule_set_id = %s""",
                    (int(vars_["max_booking_minutes"].get()),
                     int(vars_["checkin_grace_minutes"].get()),
                     int(vars_["cooldown_minutes"].get()),
                     int(vars_["cancel_cutoff_minutes"].get()),
                     int(vars_["points_no_show"].get()),
                     int(vars_["points_late_cancel"].get()),
                     int(vars_["suspension_threshold_points"].get()),
                     int(vars_["suspension_duration_days"].get()),
                     rule_set_id)
                )
                win.destroy()
                self._load_data()
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=win)

        tk.Button(win, text="SAVE", fg=WHITE, bg=MAROON,
                  font=("Poppins", 13, "bold"),
                  relief="flat", bd=0, padx=24, pady=8, cursor="hand2",
                  command=save).pack(pady=(6, 0))

    # ------------------------------------------------------------------
    def _remove_rule(self):
        sel = self.rule_tree.selection()
        if not sel:
            messagebox.showwarning("Remove", "Select a rule set first.")
            return
        rule_set_id = self.rule_tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirm", f"Remove rule set #{rule_set_id}?"):
            return
        try:
            execute_query("DELETE FROM Rules WHERE rule_set_id = %s", (rule_set_id,))
            self._load_data()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    # ------------------------------------------------------------------
    def _edit_violation(self):
        sel = self.vio_tree.selection()
        if not sel:
            messagebox.showwarning("Edit", "Select a violation first.")
            return
        vio_id  = self.vio_tree.item(sel[0])["values"][0]
        cur_st  = self.vio_tree.item(sel[0])["values"][5]

        win = tk.Toplevel(self)
        win.title("Edit Violation")
        win.geometry("340x190")
        win.configure(bg=WHITE)
        win.grab_set()

        tk.Label(win, text=f"Edit Violation #{vio_id}", fg=MAROON, bg=WHITE,
                 font=("Poppins", 15, "bold")).pack(pady=(16, 8))
        tk.Label(win, text="Status:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(anchor="w", padx=30)
        st_var = tk.StringVar(value=cur_st)
        ttk.Combobox(win, textvariable=st_var,
                     values=["open", "resolved", "appealed"],
                     state="readonly", width=20,
                     font=("Poppins", 12)
                     ).pack(anchor="w", padx=30, pady=(2, 10))

        def save():
            try:
                execute_query(
                    "UPDATE Violations SET status = %s WHERE violation_id = %s",
                    (st_var.get(), vio_id)
                )
                win.destroy()
                self._load_data()
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=win)

        tk.Button(win, text="SAVE", fg=WHITE, bg=MAROON,
                  font=("Poppins", 13, "bold"),
                  relief="flat", bd=0, padx=24, pady=8, cursor="hand2",
                  command=save).pack()
