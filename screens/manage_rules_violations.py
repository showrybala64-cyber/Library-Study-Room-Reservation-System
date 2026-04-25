# Admin policy management screen.
# Manages rule sets (booking limits, grace periods, penalty points) and provides
# the admin password reset tool that issues a temporary 'mypass' credential.
# SHA2 is used here to match MySQL's native SHA2 function, not Python's hashlib.

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date
from connect_db import execute_query, get_connection

# tkcalendar is optional; falls back to a plain CTkEntry for the date field.
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


class ManageRulesViolations(tk.Frame):
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
        content.rowconfigure(4, weight=1)

        tk.Label(content, text="Manage Rules",
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
        for lbl, cmd in [("Add Rule Set",            self._add_rule),
                          ("Edit Rule Set",           self._edit_rule),
                          ("Remove Rule Set",         self._remove_rule),
                          ("Reset Student Password",  self._open_reset_password_popup),
                          ("Refresh",                 self._load_data)]:
            bg = "#AA0000" if "Remove" in lbl else MAROON
            tk.Button(rule_btn_row, text=lbl,
                      fg=WHITE, bg=bg,
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

        self._load_data()

    def _load_data(self):
        for r in self.rule_tree.get_children():
            self.rule_tree.delete(r)

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
                "SELECT violation_id, status FROM Violations",
                fetch=True
            )

            self._stat_lbls["Total Rules"].config(text=str(len(rules)))
            self._stat_lbls["Total Violations"].config(text=str(len(vios)))
            active_v = sum(1 for r in vios if r["status"] == "active")
            self._stat_lbls["Active Violations"].config(text=str(active_v))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

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
                # Deactivate existing rules before inserting so exactly one is active at a time.
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

    # Issues a temporary password so the student can log in and set their own new password.
    def _open_reset_password_popup(self):
        import re

        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, first_name, last_name, email "
            "FROM Users WHERE role='student' ORDER BY first_name"
        )
        all_students = cursor.fetchall()
        cursor.close()
        conn.close()

        popup = tk.Toplevel(self)
        popup.title("Reset Student Password")
        popup.geometry("420x600")
        popup.resizable(False, False)
        popup.configure(bg="white")
        popup.grab_set()
        popup.update_idletasks()
        x = (popup.winfo_screenwidth()  // 2) - 210
        y = (popup.winfo_screenheight() // 2) - 300
        popup.geometry(f"420x600+{x}+{y}")

        # ── Scrollable canvas ──────────────────────────────────────────
        main_canvas = tk.Canvas(popup, bg="white", highlightthickness=0)
        vsb = tk.Scrollbar(popup, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        main_canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(main_canvas, bg="white")
        inner_window = main_canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_frame_configure(e):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))

        def on_canvas_configure(e):
            main_canvas.itemconfig(inner_window, width=e.width)

        def on_mousewheel(e):
            main_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        inner.bind("<Configure>", on_frame_configure)
        main_canvas.bind("<Configure>", on_canvas_configure)
        main_canvas.bind("<MouseWheel>", on_mousewheel)
        inner.bind("<MouseWheel>", on_mousewheel)

        selected = [None]

        # ── Title ──────────────────────────────────────────────────────
        tk.Label(inner, text="Reset Student Password",
                 font=("Poppins", 13, "bold"), bg="white", fg="#5E1219"
                 ).pack(pady=(10, 3), padx=20, anchor="w")
        tk.Frame(inner, bg="#5E1219", height=2).pack(fill="x", padx=20, pady=(0, 6))

        tk.Label(inner,
                 text="Search for a student and select them from the list.\n"
                      "Their password will be reset to the temporary password 'mypass'.\n"
                      "They will be prompted to change it on next login.",
                 font=("Poppins", 10), bg="white", fg="#666666",
                 justify="left", wraplength=370
                 ).pack(padx=20, anchor="w")
        tk.Frame(inner, bg="#DDDDDD", height=1).pack(fill="x", padx=20, pady=10)

        # ── Search ─────────────────────────────────────────────────────
        tk.Label(inner, text="Search Student:",
                 font=("Poppins", 11, "bold"), bg="white", fg="#5E1219"
                 ).pack(padx=20, pady=(6, 2), anchor="w")

        search_var   = tk.StringVar()
        search_frame = tk.Frame(inner, bg="white")
        search_frame.pack(padx=20, pady=(3, 0), fill="x")

        search_entry = tk.Entry(search_frame, textvariable=search_var,
                                font=("Poppins", 11), relief="solid", bd=1)
        search_entry.pack(side="left", fill="x", expand=True, ipady=5)

        def clear_search():
            search_var.set("")
            selected[0] = None
            update_selected_display()
            search_entry.focus_set()

        tk.Button(search_frame, text="\u2715", font=("Poppins", 10),
                  bg="white", fg="#666", relief="flat", bd=0,
                  command=clear_search).pack(side="left", padx=(4, 0))

        # ── Listbox ────────────────────────────────────────────────────
        list_frame = tk.Frame(inner, bg="white")
        list_frame.pack(padx=20, pady=(2, 0), fill="x")

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, font=("Poppins", 10),
                             height=5, relief="solid", bd=1,
                             selectbackground="#5E1219", selectforeground="white",
                             activestyle="none",
                             yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="x", expand=True)
        listbox.bind("<MouseWheel>", on_mousewheel)
        scrollbar.config(command=listbox.yview)

        def populate_listbox(students):
            listbox.delete(0, "end")
            for s in students:
                listbox.insert(
                    "end",
                    f"{s['first_name']} {s['last_name']}  (ID: {s['user_id']})"
                )

        populate_listbox(all_students)

        def on_search(*args):
            typed = search_var.get().strip().lower()
            if not typed:
                populate_listbox(all_students)
            else:
                filtered = [
                    s for s in all_students
                    if s["first_name"].lower().startswith(typed)
                    or s["last_name"].lower().startswith(typed)
                ]
                populate_listbox(filtered)

        search_var.trace_add("write", on_search)

        def on_select(event=None):
            try:
                idx = listbox.curselection()
                if not idx:
                    return
                text  = listbox.get(idx[0])
                match = re.search(r"ID:\s*(\d+)", text)
                if not match:
                    return
                uid     = int(match.group(1))
                student = next((s for s in all_students if s["user_id"] == uid), None)
                if student:
                    selected[0] = student
                    update_selected_display()
            except Exception as e:
                print(f"on_select error: {e}")

        listbox.bind("<<ListboxSelect>>", on_select)
        listbox.bind("<ButtonRelease-1>", on_select)

        tk.Frame(inner, bg="#DDDDDD", height=1).pack(fill="x", padx=20, pady=10)

        # ── Selected student display ────────────────────────────────────
        tk.Label(inner, text="Selected Student:",
                 font=("Poppins", 11, "bold"), bg="white", fg="#5E1219"
                 ).pack(padx=20, anchor="w")

        info_frame = tk.Frame(inner, bg="#FFF8E7", bd=1, relief="solid")
        info_frame.pack(padx=20, pady=(3, 0), fill="x")

        name_var  = tk.StringVar(value="No student selected")
        email_var = tk.StringVar(value="")
        id_var    = tk.StringVar(value="")

        tk.Label(info_frame, textvariable=name_var,
                 font=("Poppins", 11, "bold"), bg="#FFF8E7", fg="#5E1219",
                 anchor="w").pack(padx=10, pady=(5, 1), fill="x")
        tk.Label(info_frame, textvariable=email_var,
                 font=("Poppins", 10), bg="#FFF8E7", fg="#333333",
                 anchor="w").pack(padx=10, pady=(1, 1), fill="x")
        tk.Label(info_frame, textvariable=id_var,
                 font=("Poppins", 10), bg="#FFF8E7", fg="#333333",
                 anchor="w").pack(padx=10, pady=(1, 5), fill="x")

        def update_selected_display():
            s = selected[0]
            if s:
                name_var.set(f"{s['first_name']} {s['last_name']}")
                email_var.set(f"Email:    {s['email']}")
                id_var.set(f"User ID: {s['user_id']}")
                reset_btn.configure(state="normal", fg_color="#5E1219")
            else:
                name_var.set("No student selected")
                email_var.set("")
                id_var.set("")
                reset_btn.configure(state="disabled", fg_color="#999999")

        # ── Warning ────────────────────────────────────────────────────
        tk.Label(inner,
                 text="\u26a0  This will set the student's password to 'mypass'.\n"
                      "    They must change it on next login.",
                 font=("Poppins", 10), bg="white", fg="#CC6600",
                 justify="left").pack(padx=20, pady=(6, 0), anchor="w")

        # ── Buttons ────────────────────────────────────────────────────
        btn_frame = tk.Frame(inner, bg="white")
        btn_frame.pack(pady=(10, 15), padx=20, fill="x")

        def do_reset():
            s = selected[0]
            if not s:
                messagebox.showwarning("No Student Selected",
                                       "Please select a student first.",
                                       parent=popup)
                return
            confirm = messagebox.askyesno(
                "Confirm Password Reset",
                f"Reset password for {s['first_name']} {s['last_name']}?\n\n"
                f"Their password will be set to 'mypass'.\n"
                f"They will be required to change it on next login.",
                parent=popup
            )
            if not confirm:
                return
            try:
                conn   = get_connection()
                cursor = conn.cursor()
                # SHA2 here matches MySQL's native function; the student's reset uses Python hashlib.
                # Both produce the same SHA-256 hex digest so the two can interoperate.
                cursor.execute(
                    "UPDATE Users SET password_hash = SHA2('mypass', 256), "
                    "password_reset_required = 1 WHERE user_id = %s",
                    (s["user_id"],)
                )
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo(
                    "Password Reset",
                    f"Password for {s['first_name']} {s['last_name']} has been "
                    f"reset to 'mypass'.\n"
                    f"They will be prompted to change it on next login.",
                    parent=popup
                )
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset password:\n{e}",
                                     parent=popup)

        reset_btn = ctk.CTkButton(btn_frame, text="Reset Password",
                                  width=180, height=38,
                                  font=("Poppins", 12, "bold"),
                                  fg_color="#999999", text_color="white",
                                  state="disabled",
                                  command=do_reset)
        reset_btn.pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Cancel",
                      width=100, height=38,
                      font=("Poppins", 11),
                      fg_color="#888888", text_color="white",
                      command=popup.destroy).pack(side="left")

        popup.update_idletasks()
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        popup.after(100, lambda: main_canvas.yview_moveto(0.0))

