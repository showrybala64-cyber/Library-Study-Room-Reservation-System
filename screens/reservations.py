import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import datetime, timedelta
import pytz
from connect_db import execute_query

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"

COLS = ("Res ID", "Room", "Category", "Date", "Start", "End", "Status")


class Reservations(tk.Frame):
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

        tk.Label(content, text="My Reservations",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w")

        # Action buttons
        btn_row = tk.Frame(content, bg=WHITE)
        btn_row.grid(row=1, column=0, sticky="w", pady=(12, 8))

        for label, cmd in [
            ("Refresh",             self._load_data),
            ("Check-In",            self._check_in),
            ("Cancel Reservation",  self._cancel),
            ("Manage Reservation",  self._manage),
        ]:
            tk.Button(
                btn_row, text=label,
                fg=WHITE, bg=MAROON,
                font=("Poppins", 12, "bold"),
                relief="flat", bd=0, padx=14, pady=7, cursor="hand2",
                command=cmd
            ).pack(side="left", padx=(0, 8))

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
                                 style="Res.Treeview")
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Res.Treeview",
                    background="#FFFFFF", foreground="#000000", rowheight=30,
                    fieldbackground="#FFFFFF", bordercolor=MAROON,
                    borderwidth=2, font=("Poppins", 11))
        s.configure("Res.Treeview.Heading",
                    background=MAROON, foreground="#FFFFFF",
                    font=("Poppins", 12, "bold"), borderwidth=2, relief="groove")
        s.map("Res.Treeview",
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

        self._load_data()

    # ------------------------------------------------------------------
    def _load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = execute_query(
                """SELECT r.reservation_id, rm.room_number, rm.room_category,
                          r.reservation_date, r.start_time, r.end_time, r.status
                   FROM Reservations r
                   JOIN Rooms rm ON r.room_id = rm.room_id
                   WHERE r.user_id = %s
                   ORDER BY r.reservation_date DESC, r.start_time DESC""",
                (self.user_info["user_id"],), fetch=True
            )
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=(
                    row["reservation_id"],
                    row["room_number"],
                    row["room_category"],
                    str(row["reservation_date"]),
                    str(row["start_time"]),
                    str(row["end_time"]),
                    row["status"],
                ), tags=(tag,))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    # ------------------------------------------------------------------
    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a reservation first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def _check_in(self):
        res_id = self._selected_id()
        if res_id is None:
            return
        try:
            rules = execute_query(
                "SELECT checkin_grace_minutes FROM Rules WHERE is_active = TRUE ORDER BY rule_set_id DESC LIMIT 1",
                fetch=True
            )
            grace = rules[0]["checkin_grace_minutes"] if rules else 15

            res = execute_query(
                "SELECT start_time, reservation_date, status FROM Reservations WHERE reservation_id = %s",
                (res_id,), fetch=True
            )
            if not res:
                messagebox.showerror("Check-In", "Reservation not found.")
                return
            r = res[0]
            if r["status"] != "reserved":
                messagebox.showerror("Check-In", f"Cannot check in: status is '{r['status']}'.")
                return

            est = pytz.timezone("US/Eastern")
            now = datetime.now(est).replace(tzinfo=None)

            start_dt     = datetime.combine(r["reservation_date"],
                                            (datetime.min + r["start_time"]).time())
            checkin_open  = start_dt - timedelta(minutes=15)
            checkin_close = start_dt + timedelta(minutes=grace)

            if now < checkin_open:
                open_str = checkin_open.strftime("%I:%M %p")
                messagebox.showerror(
                    "Check-In Not Available Yet",
                    f"Check-in is not available yet.\n"
                    f"You can check in from {open_str} onwards."
                )
                return

            if now > checkin_close:
                messagebox.showinfo(
                    "Check-In",
                    "Check-in window has passed for this reservation."
                )
                return

            execute_query(
                "INSERT INTO Check_Ins (reservation_id, checkin_time) VALUES (%s, NOW())",
                (res_id,)
            )
            execute_query(
                "UPDATE Reservations SET status = 'checked_in' WHERE reservation_id = %s",
                (res_id,)
            )
            messagebox.showinfo("Check-In", "Check-in successful!")
            self._load_data()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _cancel(self):
        res_id = self._selected_id()
        if res_id is None:
            return
        try:
            rules = execute_query(
                "SELECT cancel_cutoff_minutes FROM Rules WHERE is_active = TRUE ORDER BY rule_set_id DESC LIMIT 1",
                fetch=True
            )
            cutoff_m = rules[0]["cancel_cutoff_minutes"] if rules else 60

            res = execute_query(
                "SELECT start_time, reservation_date, status FROM Reservations WHERE reservation_id = %s",
                (res_id,), fetch=True
            )
            if not res:
                messagebox.showerror("Cancel", "Reservation not found.")
                return
            r = res[0]
            if r["status"] != "reserved":
                messagebox.showerror("Cancel", f"Cannot cancel: status is '{r['status']}'.")
                return

            start_dt = datetime.combine(r["reservation_date"],
                                        (datetime.min + r["start_time"]).time())
            import datetime as dt_mod
            cutoff_dt = start_dt - dt_mod.timedelta(minutes=cutoff_m)
            now = datetime.now()

            if now > cutoff_dt:
                # Late cancel – create violation
                execute_query(
                    """INSERT INTO Violations (user_id, reservation_id, violation_type, points_assessed, status)
                       SELECT r.user_id, %s, 'late_cancel',
                              COALESCE((SELECT points_late_cancel FROM Rules
                                        WHERE is_active = TRUE
                                        ORDER BY rule_set_id DESC LIMIT 1), 5),
                              'open'
                       FROM Reservations r WHERE r.reservation_id = %s""",
                    (res_id, res_id)
                )
                messagebox.showwarning(
                    "Late Cancel",
                    f"Cancelled after the {cutoff_m}-minute cutoff. A late-cancel violation has been recorded."
                )
            else:
                messagebox.showinfo("Cancelled", "Reservation cancelled without penalty.")

            execute_query(
                "UPDATE Reservations SET status = 'cancelled', canceled_at = NOW(), "
                "canceled_by_user_id = %s WHERE reservation_id = %s",
                (self.user_info["user_id"], res_id)
            )
            self._load_data()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _manage(self):
        res_id = self._selected_id()
        if res_id is None:
            return
        messagebox.showinfo(
            "Manage",
            f"Reservation #{res_id} – to modify this reservation, please cancel and create a new one."
        )
