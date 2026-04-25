# Admin overview dashboard with filterable stat cards and three embedded charts.
# Filters are applied as a batch on Apply click rather than live so that expensive
# queries only run when the manager is ready, not on every keystroke.

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import connect_db
from components.date_picker import make_date_entry

MAROON = "#5E1219"
GOLD   = "#EFBF04"
WHITE  = "#FFFFFF"
LGRAY  = "#F5F5F5"


class ManagerDashboard(tk.Frame):
    def __init__(self, parent, user_info: dict, navigator, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.user_info = user_info
        self.navigator = navigator

        self._all_students   = []
        self._selected_uid   = None
        self._lb_matches     = []
        self._listbox_win    = None
        self._listbox        = None
        self._chart_canvases = []

        # Snapshot of committed filter values; charts and cards read from here, not live widgets.
        self._active = {"uid": None, "type": "All", "from": None, "to": None}

        self._build()
        self.after(100, self._load_students)

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        vsb = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=vsb.set)

        self._inner = tk.Frame(self._canvas, bg=WHITE)
        self._win_id = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._win_id, width=e.width))

        for w in (self._canvas, self._inner):
            w.bind("<MouseWheel>", self._on_scroll)

        self._inner.columnconfigure(0, weight=1)

        name = self.user_info.get("name", "Manager")
        tk.Label(self._inner, text="Manager Dashboard",
                 fg=MAROON, bg=WHITE, font=("Poppins", 24, "bold")
                 ).grid(row=0, column=0, sticky="w", padx=30, pady=(20, 0))
        tk.Label(self._inner, text=f"Welcome Back, {name}!",
                 fg="#333333", bg=WHITE, font=("Poppins", 16)
                 ).grid(row=1, column=0, sticky="w", padx=30, pady=(4, 10))

        self._build_filter_panel()

        self._cards_frame = tk.Frame(self._inner, bg=WHITE)
        self._cards_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(10, 10))
        for c in range(3):
            self._cards_frame.columnconfigure(c, weight=1)
        self._build_stat_cards()

        self._charts_frame = tk.Frame(self._inner, bg=WHITE)
        self._charts_frame.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 20))
        for c in range(3):
            self._charts_frame.columnconfigure(c, weight=1)
        self._build_charts()

    def _on_scroll(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_filter_panel(self):
        panel = tk.Frame(self._inner, bg=LGRAY, pady=6, padx=8)
        panel.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 5))

        lbl_font = ("Poppins", 11, "bold")
        inp_font = ("Poppins", 11)

        # -- Student field with maroon border frame + arrow indicator --
        tk.Label(panel, text="Student:", bg=LGRAY, font=lbl_font
                 ).pack(side="left", padx=(0, 3))

        student_border = tk.Frame(panel, bg=MAROON, padx=1, pady=1)
        student_border.pack(side="left", padx=(0, 3))

        student_inner = tk.Frame(student_border, bg=WHITE)
        student_inner.pack(fill="both", expand=True)

        self._student_var = tk.StringVar()
        self._student_entry = tk.Entry(
            student_inner, textvariable=self._student_var,
            width=15, font=inp_font, relief="flat", bd=0, bg=WHITE)
        self._student_entry.pack(side="left", ipady=4, padx=(4, 0))

        # Arrow button — toggles full student list
        tk.Button(student_inner, text="▼", bg=WHITE, fg=MAROON,
                  font=("Arial", 8), relief="flat", bd=0,
                  cursor="hand2",
                  command=self._toggle_all_students
                  ).pack(side="left", padx=(1, 1))

        tk.Button(student_inner, text="✕", command=self._clear_student,
                  bg=WHITE, relief="flat", font=("Poppins", 8),
                  cursor="hand2", fg="#888888").pack(side="left", padx=(0, 2))

        self._student_var.trace_add("write", self._on_student_type)
        self._student_entry.bind("<Down>",   self._lb_down)
        self._student_entry.bind("<Up>",     self._lb_up)
        self._student_entry.bind("<Return>", self._lb_enter)
        self._student_entry.bind("<Escape>", lambda e: self._close_lb())

        # -- Violation type (ttk.Combobox with styled popup) --
        tk.Label(panel, text="Type:", bg=LGRAY, font=lbl_font
                 ).pack(side="left", padx=(0, 3))
        self._type_var = tk.StringVar(value="All")

        _style = ttk.Style()
        _style.configure("Dashboard.TCombobox", font=("Poppins", 12), padding=5)
        _root = self.winfo_toplevel()
        _root.option_add("*TCombobox*Listbox.font",            ("Poppins", 12))
        _root.option_add("*TCombobox*Listbox.selectBackground", MAROON)
        _root.option_add("*TCombobox*Listbox.selectForeground", WHITE)

        type_cb = ttk.Combobox(panel, textvariable=self._type_var,
                               values=["All", "No Show", "Late Cancel"],
                               state="readonly", width=10,
                               font=("Poppins", 12),
                               style="Dashboard.TCombobox")
        type_cb.pack(side="left", padx=(0, 3))

        # -- From date --
        tk.Label(panel, text="From:", bg=LGRAY, font=lbl_font
                 ).pack(side="left", padx=(0, 3))
        self._from_date = make_date_entry(panel, bg=LGRAY, entry_width=110)
        self._from_date.pack(side="left", padx=(0, 3))

        # -- To date --
        tk.Label(panel, text="To:", bg=LGRAY, font=lbl_font
                 ).pack(side="left", padx=(0, 3))
        self._to_date = make_date_entry(panel, bg=LGRAY, entry_width=110)
        self._to_date.pack(side="left", padx=(0, 3))

        # -- Buttons --
        tk.Button(panel, text="Apply", command=self._apply_filters,
                  bg=MAROON, fg=WHITE, font=("Poppins", 11, "bold"),
                  relief="flat", width=9, pady=3, cursor="hand2"
                  ).pack(side="left", padx=(0, 4))
        tk.Button(panel, text="Reset", command=self._reset_filters,
                  bg="#AAAAAA", fg=WHITE, font=("Poppins", 11),
                  relief="flat", width=9, pady=3, cursor="hand2"
                  ).pack(side="left")

        self.bind_all("<Button-1>", self._on_global_click, "+")

    def _load_students(self):
        try:
            rows = connect_db.execute_query(
                "SELECT user_id, first_name, last_name FROM Users "
                "WHERE role='student' ORDER BY first_name",
                fetch=True)
            self._all_students = rows or []
        except Exception:
            self._all_students = []

    def _on_student_type(self, *_):
        text = self._student_var.get().strip().lower()
        if not text:
            self._close_lb()
            self._selected_uid = None
            return
        # Match only if typed text starts first_name OR last_name
        matches = [s for s in self._all_students
                   if s["first_name"].lower().startswith(text)
                   or s["last_name"].lower().startswith(text)]
        self._lb_matches = matches[:6]
        if self._lb_matches:
            self._show_lb()
        else:
            self._close_lb()

    # Arrow button shows the full student list; second click closes it.
    def _toggle_all_students(self):
        if self._listbox_win:
            self._close_lb()
        else:
            self._show_lb(matches=list(self._all_students))

    # Opens an undecorated Toplevel positioned below the entry field.
    def _show_lb(self, matches=None):
        self._close_lb()
        if matches is not None:
            self._lb_matches = matches

        if not self._lb_matches:
            return

        entry = self._student_entry
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        w = entry.winfo_width() + 50   # account for arrow + X buttons

        win = tk.Toplevel(self)
        win.wm_overrideredirect(True)

        # Outer frame gives the solid border
        outer = tk.Frame(win, relief="solid", bd=1)
        outer.pack(fill="both", expand=True)

        lb = tk.Listbox(outer, bg=WHITE, selectbackground=MAROON,
                        selectforeground=WHITE, font=("Poppins", 11),
                        relief="flat", borderwidth=0, activestyle="none")
        vsb = tk.Scrollbar(outer, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=vsb.set)

        lb.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for s in self._lb_matches:
            lb.insert("end", f"{s['first_name']} {s['last_name']}")

        lb.bind("<ButtonRelease-1>", self._lb_click)
        lb.bind("<Return>",          self._lb_enter)
        lb.bind("<Escape>",          lambda e: self._close_lb())

        visible = min(len(self._lb_matches), 8)
        row_h   = 24
        height  = visible * row_h + 4
        win.geometry(f"{w}x{height}+{x}+{y}")

        self._listbox_win = win
        self._listbox     = lb

    def _close_lb(self):
        if self._listbox_win:
            try:
                self._listbox_win.destroy()
            except Exception:
                pass
            self._listbox_win = None
            self._listbox     = None

    def _lb_click(self, _event):
        sel = self._listbox.curselection()
        if sel:
            self._pick_student(sel[0])

    def _lb_enter(self, _event):
        if self._listbox_win:
            sel = self._listbox.curselection()
            if sel:
                self._pick_student(sel[0])

    def _lb_down(self, _event):
        if not self._listbox_win:
            return
        cur = self._listbox.curselection()
        nxt = 0 if not cur else min(cur[0] + 1, len(self._lb_matches) - 1)
        self._listbox.selection_clear(0, "end")
        self._listbox.selection_set(nxt)
        self._listbox.focus_set()

    def _lb_up(self, _event):
        if not self._listbox_win:
            return
        cur = self._listbox.curselection()
        if not cur:
            return
        self._listbox.selection_clear(0, "end")
        self._listbox.selection_set(max(cur[0] - 1, 0))

    def _pick_student(self, idx):
        s = self._lb_matches[idx]
        self._selected_uid = s["user_id"]
        self._student_var.set(f"{s['first_name']} {s['last_name']}")
        self._close_lb()

    def _clear_student(self):
        self._student_var.set("")
        self._selected_uid = None
        self._close_lb()

    def _on_global_click(self, event):
        if not self._listbox_win:
            return
        try:
            win = self._listbox_win
            wx, wy = win.winfo_rootx(), win.winfo_rooty()
            ww, wh = win.winfo_width(), win.winfo_height()
            in_lb = wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh
            if not in_lb:
                ex = self._student_entry.winfo_rootx()
                ey = self._student_entry.winfo_rooty()
                ew = self._student_entry.winfo_width()
                eh = self._student_entry.winfo_height()
                in_entry = ex <= event.x_root <= ex + ew and ey <= event.y_root <= ey + eh
                if not in_entry:
                    self._close_lb()
        except Exception:
            pass

    def _apply_filters(self):
        from_str = (self._from_date.get() or "").strip() or None
        to_str   = (self._to_date.get()   or "").strip() or None
        self._active = {
            "uid":  self._selected_uid,
            "type": self._type_var.get(),
            "from": from_str,
            "to":   to_str,
        }
        self._build_stat_cards()
        self._build_charts()

    def _reset_filters(self):
        self._clear_student()
        self._type_var.set("All")
        self._from_date.entry.delete(0, "end")
        self._to_date.entry.delete(0, "end")
        self._active = {"uid": None, "type": "All", "from": None, "to": None}
        self._build_stat_cards()
        self._build_charts()

    def _build_stat_cards(self):
        for w in self._cards_frame.winfo_children():
            w.destroy()

        labels, values = self._fetch_stats()
        for col, (lbl, val) in enumerate(zip(labels, values)):
            card = tk.Frame(self._cards_frame, bg=GOLD, bd=0)
            card.grid(row=0, column=col, sticky="ew", padx=8, pady=4)
            card.columnconfigure(0, weight=1)

            tk.Label(card, text=str(val), fg=MAROON, bg=GOLD,
                     font=("Poppins", 32, "bold")
                     ).grid(row=0, column=0, padx=20, pady=(10, 2))
            tk.Label(card, text=lbl, fg=MAROON, bg=GOLD,
                     font=("Poppins", 11)
                     ).grid(row=1, column=0, padx=20, pady=(0, 10))

    # Returns different labels and queries depending on whether a specific student is selected.
    def _fetch_stats(self):
        uid = self._active["uid"]
        try:
            if uid:
                r1 = connect_db.execute_query(
                    "SELECT COUNT(*) AS cnt FROM Reservations WHERE user_id=%s",
                    (uid,), fetch=True)
                r2 = connect_db.execute_query(
                    "SELECT penalty_points FROM Users WHERE user_id=%s",
                    (uid,), fetch=True)
                r3 = connect_db.execute_query(
                    "SELECT COUNT(*) AS cnt FROM Violations "
                    "WHERE user_id=%s AND status='active'",
                    (uid,), fetch=True)
                return (
                    ["Total Reservations", "Penalty Points", "Active Violations"],
                    [r1[0]["cnt"] if r1 else 0,
                     r2[0]["penalty_points"] if r2 else 0,
                     r3[0]["cnt"] if r3 else 0],
                )
            else:
                r1 = connect_db.execute_query(
                    "SELECT COUNT(*) AS cnt FROM Rooms WHERE status='available'",
                    fetch=True)
                r2 = connect_db.execute_query(
                    "SELECT COUNT(*) AS cnt FROM Users "
                    "WHERE role='student' AND account_status='active'",
                    fetch=True)
                r3 = connect_db.execute_query(
                    "SELECT COUNT(*) AS cnt FROM Violations WHERE status='active'",
                    fetch=True)
                return (
                    ["Total Available Rooms", "Active Students", "Active Violations"],
                    [r1[0]["cnt"] if r1 else 0,
                     r2[0]["cnt"] if r2 else 0,
                     r3[0]["cnt"] if r3 else 0],
                )
        except Exception:
            return (
                ["Total Available Rooms", "Active Students", "Active Violations"],
                ["-", "-", "-"],
            )

    def _build_charts(self):
        for cv in self._chart_canvases:
            try:
                cv.get_tk_widget().destroy()
            except Exception:
                pass
        self._chart_canvases = []

        for w in self._charts_frame.winfo_children():
            w.destroy()

        uid      = self._active["uid"]
        type_val = self._active["type"]
        from_val = self._active["from"]
        to_val   = self._active["to"]

        self._chart_room_usage(0, uid, from_val, to_val)
        self._chart_penalty_dist(1, uid)
        self._chart_violations_trend(2, uid, type_val, from_val, to_val)

    def _chart_border(self, col):
        f = tk.Frame(self._charts_frame, bg=WHITE,
                     highlightbackground=MAROON, highlightthickness=1)
        f.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)
        return f

    def _chart_room_usage(self, col, uid, from_val, to_val):
        frame = self._chart_border(col)
        rows  = []
        try:
            q = (
                "SELECT r.room_number, COUNT(res.reservation_id) AS total "
                "FROM Rooms r "
                "LEFT JOIN Reservations res ON res.room_id = r.room_id "
                "WHERE 1=1"
            )
            params = []
            if uid:
                q += " AND res.user_id = %s"
                params.append(uid)
            if from_val and to_val:
                q += " AND res.reservation_date BETWEEN %s AND %s"
                params.extend([from_val, to_val])
            q += " GROUP BY r.room_id, r.room_number ORDER BY total ASC"
            rows = connect_db.execute_query(q, params or None, fetch=True) or []
        except Exception:
            pass

        fig = Figure(figsize=(5.5, 5))
        ax  = fig.add_subplot(111)

        if rows:
            rooms  = [r["room_number"] for r in rows]
            totals = [r["total"]       for r in rows]
            bars   = ax.barh(rooms, totals, color=MAROON, height=0.6)
            ax.set_yticks(range(len(rooms)))
            ax.set_yticklabels(rooms, fontsize=8)
            ax.yaxis.set_tick_params(labelleft=True)
            for label in ax.get_yticklabels():
                label.set_visible(True)
            for bar, val in zip(bars, totals):
                ax.text(bar.get_width() + 0.1,
                        bar.get_y() + bar.get_height() / 2,
                        str(val), va="center", fontsize=8)
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10, color="#888888")

        ax.set_title("Room Usage by Room", fontsize=10, color=MAROON, fontweight="bold")
        ax.set_xlabel("Reservations", fontsize=9)
        ax.set_ylabel("Room", fontsize=9)
        ax.tick_params(axis="x", labelsize=8)
        fig.subplots_adjust(left=0.18)
        fig.tight_layout(pad=1.5)

        self._embed_chart(fig, frame)

    # Compares selected student vs class average when a student is chosen; shows distribution when not.
    def _chart_penalty_dist(self, col, uid):
        frame   = self._chart_border(col)
        fig     = Figure(figsize=(5, 4))
        ax      = fig.add_subplot(111)
        no_data = False

        try:
            if uid:
                r_s = connect_db.execute_query(
                    "SELECT penalty_points FROM Users WHERE user_id=%s",
                    (uid,), fetch=True)
                r_a = connect_db.execute_query(
                    "SELECT AVG(penalty_points) AS avg_pts "
                    "FROM Users WHERE role='student'",
                    fetch=True)
                if not r_s:
                    no_data = True
                else:
                    sp = int(r_s[0]["penalty_points"] or 0)
                    ap = round(float(r_a[0]["avg_pts"] or 0), 1) if r_a else 0.0
                    bars = ax.bar(["Selected Student", "Class Average"],
                                  [sp, ap], color=[MAROON, "#AAAAAA"])
                    for bar, v in zip(bars, [sp, ap]):
                        ax.text(bar.get_x() + bar.get_width() / 2,
                                bar.get_height() + 0.3,
                                str(v), ha="center", va="bottom", fontsize=9)
                    if max(sp, ap) > 0:
                        ax.set_ylim(0, max(sp, ap) * 1.15)
            else:
                r = connect_db.execute_query(
                    "SELECT "
                    "  SUM(CASE WHEN penalty_points = 0 THEN 1 ELSE 0 END) AS clean, "
                    "  SUM(CASE WHEN penalty_points BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS low, "
                    "  SUM(CASE WHEN penalty_points BETWEEN 6 AND 9 THEN 1 ELSE 0 END) AS medium, "
                    "  SUM(CASE WHEN penalty_points >= 10 THEN 1 ELSE 0 END) AS high "
                    "FROM Users WHERE role='student'",
                    fetch=True)
                if not r:
                    no_data = True
                else:
                    row    = r[0]
                    cats   = ["Clean\n(0pts)", "Low\n(1-5pts)", "Medium\n(6-9pts)", "High\n(10+pts)"]
                    counts = [int(row.get("clean") or 0), int(row.get("low") or 0),
                              int(row.get("medium") or 0), int(row.get("high") or 0)]
                    colors = ["#2ecc71", GOLD, "#e67e22", "#e74c3c"]
                    bars   = ax.bar(cats, counts, color=colors)
                    for bar, v in zip(bars, counts):
                        ax.text(bar.get_x() + bar.get_width() / 2,
                                bar.get_height() + 0.3,
                                str(v), ha="center", va="bottom", fontsize=9)
                    if max(counts) > 0:
                        ax.set_ylim(0, max(counts) * 1.15)
        except Exception:
            no_data = True

        if no_data:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10, color="#888888")

        ax.set_title("Student Penalty Distribution", fontsize=10, color=MAROON, fontweight="bold")
        ax.set_ylabel("Students", fontsize=9)
        ax.tick_params(labelsize=8)
        fig.tight_layout(pad=1.5)

        self._embed_chart(fig, frame)

    def _chart_violations_trend(self, col, uid, type_val, from_val, to_val):
        frame = self._chart_border(col)

        # Default to last 6 months so the chart is never empty on first load.
        if not (from_val and to_val):
            from_val = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
            to_val   = datetime.now().strftime("%Y-%m-%d")

        rows = []
        try:
            q = (
                "SELECT DATE_FORMAT(created_at,'%Y-%m') AS month, "
                "  SUM(CASE WHEN violation_type='no_show'     THEN 1 ELSE 0 END) AS no_shows, "
                "  SUM(CASE WHEN violation_type='late_cancel' THEN 1 ELSE 0 END) AS late_cancels "
                "FROM Violations WHERE 1=1"
            )
            params = []
            if uid:
                q += " AND user_id = %s"
                params.append(uid)
            if type_val and type_val != "All":
                vtype = "no_show" if type_val == "No Show" else "late_cancel"
                q += " AND violation_type = %s"
                params.append(vtype)
            q += " AND created_at BETWEEN %s AND %s"
            params.extend([from_val, to_val])
            q += " GROUP BY DATE_FORMAT(created_at,'%Y-%m') ORDER BY month ASC"
            rows = connect_db.execute_query(q, params, fetch=True) or []
        except Exception:
            pass

        fig = Figure(figsize=(5, 4))
        ax  = fig.add_subplot(111)

        if rows:
            raw_months   = [r["month"]       for r in rows]
            no_shows     = [int(r["no_shows"]     or 0) for r in rows]
            late_cancels = [int(r["late_cancels"] or 0) for r in rows]

            labels = []
            for m in raw_months:
                try:
                    labels.append(datetime.strptime(m, "%Y-%m").strftime("%b %y"))
                except Exception:
                    labels.append(m)

            x_pos     = list(range(len(labels)))
            all_lines = []
            all_data  = []

            if type_val != "Late Cancel":
                line1, = ax.plot(x_pos, no_shows, color=MAROON, marker="o",
                                 linewidth=1.5, label="No Shows")
                all_lines.append(line1)
                all_data.append((x_pos, no_shows, "No Shows"))

            if type_val != "No Show":
                line2, = ax.plot(x_pos, late_cancels, color=GOLD, marker="o",
                                 linewidth=1.5, label="Late Cancels")
                all_lines.append(line2)
                all_data.append((x_pos, late_cancels, "Late Cancels"))

            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            ax.tick_params(axis="y", labelsize=8)
            ax.legend(fontsize=8)
            ax.grid(color="#E0E0E0", linestyle="--", linewidth=0.5)

            # Hover tooltip
            annot = ax.annotate(
                "", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.3", fc=MAROON, alpha=0.8),
                arrowprops=dict(arrowstyle="->", color="white"),
                color="white", fontsize=9)
            annot.set_visible(False)

            def on_hover(event):
                if event.inaxes != ax:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
                    return
                for line, (xdata, ydata, label) in zip(all_lines, all_data):
                    cont, ind = line.contains(event)
                    if cont:
                        idx   = ind["ind"][0]
                        x_val = xdata[idx]
                        y_val = ydata[idx]
                        annot.xy = (x_val, y_val)
                        annot.set_text(f"{label}\n{y_val}")
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
                annot.set_visible(False)
                fig.canvas.draw_idle()

            fig.canvas.mpl_connect("motion_notify_event", on_hover)
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10, color="#888888")

        ax.set_title("Violations by Month", fontsize=10, color=MAROON, fontweight="bold")
        ax.set_ylabel("Count", fontsize=9)
        fig.tight_layout(pad=1.5)

        self._embed_chart(fig, frame)

    def _embed_chart(self, fig, frame):
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas)
